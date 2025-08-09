from pyramid.config import Configurator
from pyramid.response import Response
from pyramid.view import view_config
from wsgiref.simple_server import make_server
import logging
import datetime
import os
import uuid
import json
from PIL import Image, ImageDraw, ImageFont
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
import queue
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Global flag to control image generation
GENERATE_IMAGES = True

# Create directories if they don't exist
os.makedirs("logs", exist_ok=True)
if GENERATE_IMAGES:
    os.makedirs("images", exist_ok=True)

# SQLAlchemy setup
Base = declarative_base()


class Paste(Base):
    __tablename__ = "pastes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


# Database setup
engine = create_engine("sqlite:///pastebin.db", echo=False)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# Global request counter with thread safety
request_counter = 0
counter_lock = threading.Lock()

# Thread pool for file generation
WORKER_COUNT = multiprocessing.cpu_count()
file_worker_pool = ThreadPoolExecutor(
    max_workers=WORKER_COUNT, thread_name_prefix="FileWorker"
)
logger.info(f"Starting {WORKER_COUNT} file generation workers")


class BitmapGenerator:
    def __init__(self, font_size=12, char_width=7, line_height=14):
        self.font_size = font_size
        self.char_width = char_width
        self.line_height = line_height

        # Try to use a monospaced font
        try:
            self.font = ImageFont.truetype(
                "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
                font_size,
            )
        except:
            try:
                self.font = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", font_size
                )
            except:
                self.font = ImageFont.load_default()

    def get_text_width(self, text):
        """Get actual pixel width of text using font metrics"""
        bbox = self.font.getbbox(text)
        return bbox[2] - bbox[0]

    def wrap_text(self, text, max_width_pixels):
        """Wrap text to fit within max_width_pixels"""
        if self.get_text_width(text) <= max_width_pixels:
            return [text]

        wrapped_lines = []
        words = text.split(" ")
        current_line = ""

        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if self.get_text_width(test_line) <= max_width_pixels:
                current_line = test_line
            else:
                if current_line:
                    wrapped_lines.append(current_line)
                    current_line = word
                else:
                    # Single word is too long, force break
                    wrapped_lines.append(word)
                    current_line = ""

        if current_line:
            wrapped_lines.append(current_line)

        return wrapped_lines

    def create_bitmap(self, log_data, bitmap_path):
        """Create a grayscale bitmap from log data"""
        # Calculate max pixel width for text (800px minus padding)
        max_text_width = 800 - 20

        # Define consistent field order with enhanced fields
        field_order = [
            "Timestamp",
            "Request ID", 
            "Endpoint",
            "Method",
            "URL",
            "Client Address",
            "User-Agent",
            "POST_Body",
            "Content_Length",
            "Content_Type", 
            "Query_String",
            "Query_Params",
            "Response_Status",
            "Response_Content_Type",
            "Error_Response",
            "Headers",
        ]

        # Build text lines with wrapping
        lines = []
        for field in field_order:
            if field in log_data:
                if field == "Headers":
                    lines.append(f"{field}:")
                    for header in log_data[field]:
                        header_line = f"  {header}"
                        wrapped = self.wrap_text(header_line, max_text_width)
                        lines.extend(wrapped)
                elif field == "POST_Body":
                    lines.append(f"POST Body Content:")
                    body_lines = str(log_data[field]).split('\n')
                    for body_line in body_lines:
                        if body_line.strip():  # Skip empty lines
                            content_line = f"  {body_line}"
                            wrapped = self.wrap_text(content_line, max_text_width)
                            lines.extend(wrapped)
                elif field == "Error_Response":
                    lines.append(f"Error Response:")
                    error_line = f"  {log_data[field]}"
                    wrapped = self.wrap_text(error_line, max_text_width)
                    lines.extend(wrapped)
                else:
                    field_line = f"{field}: {log_data[field]}"
                    wrapped = self.wrap_text(field_line, max_text_width)
                    lines.extend(wrapped)

        # Fixed width of 800px
        width = 800
        height = len(lines) * self.line_height + 20

        # Create grayscale image
        img = Image.new("L", (width, height), color=255)
        draw = ImageDraw.Draw(img)

        # Draw text
        y_position = 10
        for line in lines:
            draw.text((10, y_position), line, font=self.font, fill=0)
            y_position += self.line_height

        # Save as BMP
        img.save(bitmap_path, "BMP")

        # Also save as JPEG with very high quality
        jpeg_path = str(bitmap_path).replace(".bmp", ".jpg")
        img.save(jpeg_path, "JPEG", quality=98)

        # Save as PNG (lossless compression)
        png_path = str(bitmap_path).replace(".bmp", ".png")
        img.save(png_path, "PNG")

        # Save as WebP (better compression than JPEG)
        webp_path = str(bitmap_path).replace(".bmp", ".webp")
        img.save(webp_path, "WebP", quality=95, lossless=False)


# Initialize bitmap generator
bitmap_gen = BitmapGenerator()


def generate_files_worker(log_data, filename, bitmap_filename):
    """Worker function to generate log and image files"""
    try:
        # Write enhanced log file
        with open(filename, "w") as f:
            f.write(f"Timestamp: {log_data['Timestamp']}\n")
            f.write(f"Request ID: {log_data['Request ID']}\n")
            f.write(f"Endpoint: {log_data['Endpoint']}\n")
            f.write(f"Client Address: {log_data['Client Address']}\n")
            f.write(f"User-Agent: {log_data['User-Agent']}\n")
            f.write(f"Method: {log_data['Method']}\n")
            f.write(f"URL: {log_data['URL']}\n")
            
            # Write POST body content if present
            if "POST_Body" in log_data:
                f.write(f"POST Body Content:\n")
                f.write(f"  {log_data['POST_Body']}\n")
                f.write(f"Content-Length: {log_data.get('Content_Length', 'Unknown')}\n")
                f.write(f"Content-Type: {log_data.get('Content_Type', 'Unknown')}\n")
            
            # Write query parameters if present
            if "Query_String" in log_data:
                f.write(f"Query String: {log_data['Query_String']}\n")
            elif "Query_Params" in log_data:
                f.write(f"Query Parameters: {log_data['Query_Params']}\n")
            
            # Write response details if present
            if "Response_Status" in log_data:
                f.write(f"Response Status: {log_data['Response_Status']}\n")
                f.write(f"Response Content-Type: {log_data.get('Response_Content_Type', 'Unknown')}\n")
            
            if "Error_Response" in log_data:
                f.write(f"Error Response:\n")
                f.write(f"  {log_data['Error_Response']}\n")
            
            f.write(f"Headers:\n")
            for header in log_data["Headers"]:
                f.write(f"  {header}\n")

        # Create all image formats only if enabled
        if GENERATE_IMAGES:
            bitmap_gen.create_bitmap(log_data, bitmap_filename)

        if GENERATE_IMAGES:
            logger.info(
                f"Generated files for request ID {log_data['Request ID']} "
                f"(worker: {threading.current_thread().name})"
            )
        else:
            logger.info(
                f"Generated log file for request ID {log_data['Request ID']} "
                f"(worker: {threading.current_thread().name})"
            )

    except Exception as e:
        logger.error(f"Error generating files for {log_data['Request ID']}: {e}")


def request_counter_middleware(handler, registry):
    """Middleware to count requests and log all requests"""

    def middleware(request):
        global request_counter
        with counter_lock:
            request_counter += 1
            request.request_number = request_counter
        
        # Log all requests, including 404s
        endpoint = request.path_info or request.path
        log_request(request, endpoint)
        
        return handler(request)

    return middleware


def log_request(request, endpoint, response=None):
    """Log each request to a separate file and create bitmap (async)"""
    user_agent = request.headers.get("User-Agent", "Unknown")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    request_id = str(uuid.uuid4())[:8]
    request_num = getattr(request, "request_number", 0)

    # Include request number at the beginning of filenames
    filename = f"logs/{request_num:06d}_request_{timestamp}_{request_id}.log"
    bitmap_filename = f"images/{request_num:06d}_request_{timestamp}_{request_id}.bmp"

    # Prepare enhanced log data
    log_data = {
        "Timestamp": datetime.datetime.now().isoformat(),
        "Request ID": request_id,
        "Endpoint": endpoint,
        "Client Address": request.client_addr,
        "User-Agent": user_agent,
        "Method": request.method,
        "URL": request.url,
        "Headers": [],
    }

    # Collect and sort headers
    headers = []
    for header, value in request.headers.items():
        headers.append(f"{header}: {value}")
    headers.sort()
    log_data["Headers"] = headers

    # Enhanced logging: POST body content
    if request.method == "POST":
        try:
            # Capture POST body content
            if hasattr(request, 'text') and request.text:
                post_content = request.text[:2000]  # Limit to 2KB
            elif hasattr(request, 'body') and request.body:
                body = request.body
                if isinstance(body, bytes):
                    post_content = body.decode('utf-8', errors='ignore')[:2000]
                else:
                    post_content = str(body)[:2000]
            else:
                post_content = "[No POST body content]"
            
            log_data["POST_Body"] = post_content
            log_data["Content_Length"] = request.headers.get("Content-Length", "0")
            log_data["Content_Type"] = request.headers.get("Content-Type", "Unknown")
        except Exception as e:
            log_data["POST_Body"] = f"[Error reading POST body: {str(e)}]"

    # Enhanced logging: Query parameters  
    if hasattr(request, 'query_string') and request.query_string:
        log_data["Query_String"] = request.query_string.decode('utf-8', errors='ignore')
    elif hasattr(request, 'GET') and request.GET:
        query_params = []
        for key, value in request.GET.items():
            query_params.append(f"{key}={value}")
        if query_params:
            log_data["Query_Params"] = "&".join(query_params)

    # Enhanced logging: Response details (if provided)
    if response is not None:
        log_data["Response_Status"] = getattr(response, 'status_code', 'Unknown')
        log_data["Response_Content_Type"] = getattr(response, 'content_type', 'Unknown')
        
        # Log error responses in detail
        if hasattr(response, 'status_code') and response.status_code >= 400:
            try:
                if hasattr(response, 'text') and len(str(response.text)) < 1000:
                    log_data["Error_Response"] = str(response.text)[:500]
                elif hasattr(response, 'body') and response.body:
                    log_data["Error_Response"] = str(response.body)[:500]
                else:
                    log_data["Error_Response"] = f"HTTP {response.status_code} Error"
            except:
                log_data["Error_Response"] = f"HTTP {response.status_code} Error"


    # Submit work to thread pool (non-blocking)
    future = file_worker_pool.submit(
        generate_files_worker, log_data, filename, bitmap_filename
    )

    # Log the request immediately (without waiting for file generation)
    logger.info(
        f"Request #{request_num} to {endpoint} from {request.client_addr} "
        f"with User-Agent: {user_agent} - Queued for processing (ID: {request_id})"
    )


@view_config(route_name="home")
def home_view(request):
    return Response("Welcome to the home page!")


@view_config(route_name="hello")
def hello_view(request):
    return Response("Hello, World!")


@view_config(route_name="insert", request_method="POST")
def insert_view(request):

    try:
        # Get the raw body content - handle different ways the data might come in
        if hasattr(request, 'text') and request.text:
            content = request.text
        elif request.content_type and 'application/x-www-form-urlencoded' in request.content_type:
            # Handle form data
            content = '\n'.join([f"{k}: {v}" for k, v in request.POST.items()])
        else:
            # Handle raw body content
            body = request.body
            if isinstance(body, bytes):
                content = body.decode('utf-8', errors='ignore')
            else:
                content = str(body)

        # Store in database
        session = Session()
        paste = Paste(content=content)
        session.add(paste)
        session.commit()
        paste_id = paste.id
        session.close()

        # Return JSON response
        response_data = {
            "success": True,
            "id": paste_id,
            "message": f"Paste created with ID {paste_id}",
        }

        return Response(json.dumps(response_data), content_type="application/json; charset=utf-8")

    except Exception as e:
        logger.error(f"Error inserting paste: {e}")
        response_data = {"success": False, "error": str(e)}
        return Response(
            json.dumps(response_data), content_type="application/json; charset=utf-8", status=500
        )


@view_config(route_name="pastebin_list")
def pastebin_list_view(request):

    try:
        session = Session()
        pastes = session.query(Paste).order_by(Paste.created_at.desc()).limit(50).all()

        paste_list = []
        for paste in pastes:
            paste_list.append(
                {
                    "id": paste.id,
                    "created_at": paste.created_at.isoformat(),
                    "preview": paste.content[:100]
                    + ("..." if len(paste.content) > 100 else ""),
                }
            )

        session.close()

        return Response(
            json.dumps(paste_list, indent=2), content_type="application/json; charset=utf-8"
        )

    except Exception as e:
        logger.error(f"Error listing pastes: {e}")
        return Response(
            json.dumps({"error": str(e)}), content_type="application/json; charset=utf-8", status=500
        )


@view_config(route_name="pastebin_get")
def pastebin_get_view(request):
    paste_id = request.matchdict["id"]

    try:
        session = Session()
        paste = session.query(Paste).filter(Paste.id == int(paste_id)).first()
        session.close()

        if paste is None:
            return Response("Paste not found", status=404, content_type="text/plain")

        return Response(paste.content, content_type="text/plain")

    except ValueError:
        return Response("Invalid paste ID", status=400, content_type="text/plain")
    except Exception as e:
        logger.error(f"Error retrieving paste {paste_id}: {e}")
        return Response(f"Error: {str(e)}", status=500, content_type="text/plain")


def main():
    global GENERATE_IMAGES
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Pyramid web server with request logging")
    parser.add_argument('--no-images', action='store_true', help='Disable image generation')
    args = parser.parse_args()
    
    # Set image generation flag
    GENERATE_IMAGES = not args.no_images
    
    if not GENERATE_IMAGES:
        logger.info("Image generation is DISABLED")
    else:
        logger.info("Image generation is ENABLED")
    
    config = Configurator()

    # Add request counter middleware
    config.add_tween("__main__.request_counter_middleware")

    config.add_route("home", "/")
    config.add_route("hello", "/hello")
    config.add_route("insert", "/insert")
    config.add_route("pastebin_list", "/pastebin")
    config.add_route("pastebin_get", "/pastebin/{id}")
    config.scan()

    app = config.make_wsgi_app()
    server = make_server("localhost", 6543, app)
    print(
        f"Server started at http://localhost:6543 with {WORKER_COUNT} file generation workers"
    )

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        file_worker_pool.shutdown(wait=True)
        print("All workers completed. Server stopped.")


if __name__ == "__main__":
    main()
