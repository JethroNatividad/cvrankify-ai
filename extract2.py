from doctr.models import ocr_predictor
from doctr.io import DocumentFile
from utils import extract_pdf_text
import numpy as np


def extract_text_with_column_awareness(structured_output):
    """
    Extract text from doctr output while handling multi-column layouts.
    Sorts blocks by position to maintain reading order.
    """
    text = ""

    for page in structured_output["pages"]:
        # Collect all blocks with their positions
        blocks_with_pos = []
        for block in page["blocks"]:
            if block["lines"]:  # Only process blocks that have text
                # Get block position (top-left corner)
                block_geometry = block["geometry"]
                # doctr geometry is normalized [0,1]
                top = block_geometry[0][1]  # y-coordinate of top-left
                left = block_geometry[0][0]  # x-coordinate of top-left

                # Extract text from this block
                block_text = ""
                for line in block["lines"]:
                    line_text = " ".join([word["value"] for word in line["words"]])
                    if line_text.strip():
                        block_text += line_text + "\n"

                if block_text.strip():
                    blocks_with_pos.append(
                        {"text": block_text, "top": top, "left": left}
                    )

        # Sort blocks by reading order (top to bottom, then left to right)
        # Use a tolerance for "same row" to handle slight vertical misalignments
        tolerance = 0.05  # 5% tolerance for same row

        # Group blocks by approximate rows
        rows = []
        for block in blocks_with_pos:
            placed = False
            for row in rows:
                # Check if block belongs to existing row (similar top position)
                if abs(block["top"] - row[0]["top"]) <= tolerance:
                    row.append(block)
                    placed = True
                    break
            if not placed:
                rows.append([block])

        # Sort rows by top position, and blocks within each row by left position
        rows.sort(key=lambda row: row[0]["top"])
        for row in rows:
            row.sort(key=lambda block: block["left"])

        # Concatenate text maintaining proper order
        for row in rows:
            for block in row:
                text += block["text"]
            text += "\n"  # Add extra line break between rows

    return text.strip()


def detect_columns_and_extract(structured_output):
    """
    Advanced column detection and text extraction for multi-column layouts.
    """
    text = ""

    for page in structured_output["pages"]:
        # Collect all blocks with detailed position info
        blocks_with_pos = []
        for block in page["blocks"]:
            if block["lines"]:
                block_geometry = block["geometry"]
                top = block_geometry[0][1]
                left = block_geometry[0][0]
                bottom = block_geometry[1][1]
                right = block_geometry[1][0]
                width = right - left
                height = bottom - top

                block_text = ""
                for line in block["lines"]:
                    line_text = " ".join([word["value"] for word in line["words"]])
                    if line_text.strip():
                        block_text += line_text + "\n"

                if block_text.strip():
                    blocks_with_pos.append(
                        {
                            "text": block_text,
                            "top": top,
                            "left": left,
                            "bottom": bottom,
                            "right": right,
                            "width": width,
                            "height": height,
                            "center_x": left + width / 2,
                        }
                    )

        if not blocks_with_pos:
            continue

        # Debug: Print block positions
        print("DEBUG: Block positions:")
        for i, block in enumerate(blocks_with_pos):
            print(
                f"Block {i}: left={block['left']:.3f}, center_x={block['center_x']:.3f}, text_preview='{block['text'][:30].replace(chr(10), ' ')}...'"
            )

        # More sophisticated column detection
        # Sort blocks by left position to find natural column breaks
        blocks_by_left = sorted(blocks_with_pos, key=lambda b: b["left"])

        # Find significant gaps in the left positions
        column_starts = [0.0]  # Always start with left margin

        for i in range(1, len(blocks_by_left)):
            prev_right = blocks_by_left[i - 1]["right"]
            curr_left = blocks_by_left[i]["left"]
            gap = curr_left - prev_right

            # If there's a significant gap (> 5% of page width), it's likely a column boundary
            if gap > 0.05:
                # Add the midpoint as column boundary
                column_starts.append((prev_right + curr_left) / 2)

        # Remove duplicates and sort
        column_starts = sorted(list(set(column_starts)))
        column_starts.append(1.0)  # End of page

        print(f"DEBUG: Detected column boundaries at: {column_starts}")

        # Assign blocks to columns based on their center position
        columns = [[] for _ in range(len(column_starts) - 1)]

        for block in blocks_with_pos:
            block_center = block["center_x"]
            assigned = False

            for col_idx in range(len(column_starts) - 1):
                col_start = column_starts[col_idx]
                col_end = column_starts[col_idx + 1]

                if col_start <= block_center < col_end:
                    columns[col_idx].append(block)
                    assigned = True
                    break

            if not assigned:
                # Fallback: assign to the last column
                columns[-1].append(block)

        # Debug: Show column assignments
        for col_idx, col in enumerate(columns):
            print(f"DEBUG: Column {col_idx} has {len(col)} blocks")

        # Sort blocks within each column by vertical position (top to bottom)
        for column in columns:
            column.sort(key=lambda block: block["top"])

        # Process columns separately to maintain proper column order
        column_texts = []
        for col_idx, col in enumerate(columns):
            if col:
                col_text = ""
                for block in col:
                    col_text += block["text"]
                column_texts.append(col_text.strip())

        # Join columns with clear separators
        if len(column_texts) > 1:
            # For multi-column layout, process column by column
            for i, col_text in enumerate(column_texts):
                text += f"=== COLUMN {i+1} ===\n"
                text += col_text + "\n\n"
        else:
            # Single column, just add the text
            text += column_texts[0] if column_texts else ""

    return text.strip()


def extract_text_word_level_columns(path, debug=False):
    """
    Extract text by analyzing individual words and their positions to handle multi-column layouts.
    This works better when OCR treats multiple columns as a single block.
    """

    model = ocr_predictor(pretrained=True, assume_straight_pages=False)
    # PDF
    doc = DocumentFile.from_pdf(path)
    # Analyze
    result = model(doc)

    structured_output = result.export()
    text = ""

    for page in structured_output["pages"]:
        # Collect all words with their positions
        words_with_pos = []

        for block in page["blocks"]:
            for line in block["lines"]:
                for word in line["words"]:
                    if word["value"].strip():  # Only non-empty words
                        word_geometry = word["geometry"]
                        word_left = word_geometry[0][0]
                        word_top = word_geometry[0][1]
                        word_right = word_geometry[1][0]
                        word_bottom = word_geometry[1][1]
                        word_center_x = (word_left + word_right) / 2

                        words_with_pos.append(
                            {
                                "text": word["value"],
                                "left": word_left,
                                "top": word_top,
                                "right": word_right,
                                "bottom": word_bottom,
                                "center_x": word_center_x,
                                "width": word_right - word_left,
                            }
                        )

        if not words_with_pos:
            continue

        # Analyze x-position distribution to detect columns
        x_positions = [w["center_x"] for w in words_with_pos]
        x_positions.sort()

        # Find the main gap that indicates column separation
        # Look for the largest gap in x-positions
        max_gap = 0
        column_boundary = None

        for i in range(1, len(x_positions)):
            gap = x_positions[i] - x_positions[i - 1]
            if gap > max_gap:
                max_gap = gap
                column_boundary = (x_positions[i] + x_positions[i - 1]) / 2

        if debug:
            print(
                f"DEBUG: Largest gap is {max_gap:.3f} at position {column_boundary:.3f}"
            )

        # If there's a significant gap (> 5% of page width), treat as multi-column
        if max_gap > 0.05:
            if debug:
                print("DEBUG: Multi-column layout detected")

            # Separate words into left and right columns
            left_column_words = [
                w for w in words_with_pos if w["center_x"] < column_boundary
            ]
            right_column_words = [
                w for w in words_with_pos if w["center_x"] >= column_boundary
            ]

            def reconstruct_text_from_words(words):
                if not words:
                    return ""

                # Sort words by position (top to bottom, left to right)
                words.sort(key=lambda w: (w["top"], w["left"]))

                # Group words into lines based on vertical position
                lines = []
                current_line = []
                line_threshold = 0.015  # 1.5% tolerance for same line

                for word in words:
                    if not current_line:
                        current_line = [word]
                    else:
                        # Check if word is on the same line as current line
                        avg_top = sum(w["top"] for w in current_line) / len(
                            current_line
                        )
                        if abs(word["top"] - avg_top) <= line_threshold:
                            current_line.append(word)
                        else:
                            # Finish current line and start new one
                            if current_line:
                                current_line.sort(
                                    key=lambda w: w["left"]
                                )  # Sort words in line left to right
                                lines.append(current_line)
                            current_line = [word]

                # Don't forget the last line
                if current_line:
                    current_line.sort(key=lambda w: w["left"])
                    lines.append(current_line)

                # Build text from lines
                result = ""
                for line in lines:
                    line_text = " ".join([w["text"] for w in line])
                    result += line_text + "\n"

                return result.strip()

            left_text = reconstruct_text_from_words(left_column_words)
            right_text = reconstruct_text_from_words(right_column_words)

            if debug:
                print(f"DEBUG: Left column: {len(left_column_words)} words")
                print(f"DEBUG: Right column: {len(right_column_words)} words")

            # For now, combine columns side by side - you can modify this format as needed
            text += left_text + "\n\n" + right_text + "\n"

        else:
            if debug:
                print("DEBUG: Single column layout detected")
            # Single column - reconstruct normally
            words_with_pos.sort(key=lambda w: (w["top"], w["left"]))

            lines = []
            current_line = []
            line_threshold = 0.015

            for word in words_with_pos:
                if not current_line:
                    current_line = [word]
                else:
                    avg_top = sum(w["top"] for w in current_line) / len(current_line)
                    if abs(word["top"] - avg_top) <= line_threshold:
                        current_line.append(word)
                    else:
                        if current_line:
                            current_line.sort(key=lambda w: w["left"])
                            lines.append(current_line)
                        current_line = [word]

            if current_line:
                current_line.sort(key=lambda w: w["left"])
                lines.append(current_line)

            for line in lines:
                line_text = " ".join([w["text"] for w in line])
                text += line_text + "\n"

    return text.strip()


# # test on resumes/in.pdf
# pdf_text = extract_text_word_level_columns("resumes/in.pdf", debug=True)
# print(pdf_text)
