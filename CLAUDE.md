# Claude Code Notes

## BMP to JPG Conversion Requirement

Claude Code's API cannot read BMP (bitmap) files directly. When attempting to read a BMP file, it returns the following error:

```
API Error: 400 {"type":"error","error":{"type":"invalid_request_error","message":"messages.106.content.0.tool_result.content.0.image.source.base64.media_type: Input should be 'image/jpeg', 'image/png', 'image/gif' or 'image/webp'"}}
```

### Solution

A BMP to JPG converter utility has been created in `utils/bmp_to_jpg.py` specifically to allow Claude Code to view the bitmap data.

### Usage

1. **Convert single BMP file:**
   ```bash
   python3 utils/bmp_to_jpg.py image.bmp
   ```

2. **Convert all BMPs in a directory:**
   ```bash
   python3 utils/bmp_to_jpg.py -d bitmaps/ -o jpgs/
   ```

3. **Adjust quality (default 95):**
   ```bash
   python3 utils/bmp_to_jpg.py image.bmp -q 90
   ```

### Important Notes

- The JPG conversion is purely for Claude Code viewing purposes
- The original BMP files contain the actual data and should be preserved
- The BMP generation parameters (font size, character width, line height) have been optimized to fit more text content in the images

## Git Commit Messages

When making commits, do not include Claude Code attribution (e.g., "🤖 Generated with Claude Code" or "Co-Authored-By: Claude") in commit messages. Keep commit messages clean and focused on the changes made.

## Scientific Method and Model Improvements

When improving machine learning models, follow proper scientific methodology:

1. **Isolate Variables**: Only change ONE thing at a time when testing improvements
   - If testing new feature extraction, don't also change the algorithm
   - If testing a new algorithm, keep the same features and data
   - If augmenting data, keep the model architecture constant

2. **Baseline Comparison**: Always compare against the current baseline before making changes

3. **Measure Impact**: Test each change in isolation to understand its specific effect

4. **Document Results**: Record what worked and what didn't for future reference

This ensures we can properly attribute performance changes to specific modifications rather than confounding multiple variables.