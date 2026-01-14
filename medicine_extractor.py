import cv2
import easyocr
import numpy as np
from PIL import Image
import re
import os
from collections import Counter

class MediScanExtractor:
    def __init__(self):
        """Initialize EasyOCR reader - optimized for M1 Mac"""
        print("🚀 Initializing AI Model (this may take a moment)...")
        # EasyOCR with GPU support on M1 if available
        self.reader = easyocr.Reader(['en'], gpu=False)
        print("✅ AI Model Ready!")
        
    def deskew_image(self, image):
      """Detect and correct image rotation"""
      try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # Detect edges
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Detect lines using Hough Transform
        lines = cv2.HoughLines(edges, 1, np.pi/180, 200)
        
        if lines is not None and len(lines) > 0:
            # Calculate average angle
            angles = []
            for line in lines[:20]:  # Use first 20 lines
                rho, theta = line[0]  # Extract from nested array
                angle = np.degrees(theta) - 90
                angles.append(angle)
            
            if angles: 
                median_angle = np.median(angles)
                
                # Only rotate if angle is significant
                if abs(median_angle) > 0.5:
                    # Rotate image
                    (h, w) = image.shape[:2]
                    center = (w // 2, h // 2)
                    M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                    rotated = cv2.warpAffine(image, M, (w, h), 
                                            flags=cv2.INTER_CUBIC, 
                                            borderMode=cv2.BORDER_REPLICATE)
                    return rotated
      except Exception as e:
        print(f"    ⚠️ Deskew failed: {e}, using original image")
    
      return image
    
    def preprocess_image(self, image_path):
        """Advanced image preprocessing with multiple strategies"""
        # Read image
        img = cv2.imread(image_path)
        
        if img is None:
            raise ValueError("Could not read image")
        
        # Resize if needed
        height, width = img.shape[:2]
        max_dimension = 2048
        
        if max(height, width) > max_dimension:
            scale = max_dimension / max(height, width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
        elif max(height, width) < 800:
            # Upscale small images
            scale = 800 / max(height, width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        original = img.copy()
        
        # Try to deskew
        deskewed = self.deskew_image(img)
        
        # Create multiple preprocessed versions
        preprocessed_images = []
        
        # Version 1: Original high quality
        preprocessed_images.append(("original", original))
        
        # Version 2: Deskewed
        if not np.array_equal(deskewed, img):
            preprocessed_images. append(("deskewed", deskewed))
        
        # Work with deskewed for further processing
        working_img = deskewed
        
        # Version 3: White background enhancement
        # This helps with colorful packaging
        lab = cv2.cvtColor(working_img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        cl = clahe.apply(l)
        enhanced_lab = cv2.merge((cl,a,b))
        enhanced_bgr = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        gray_enhanced = cv2.cvtColor(enhanced_bgr, cv2.COLOR_BGR2GRAY)
        preprocessed_images.append(("lab_enhanced", gray_enhanced))
        
        # Version 4: Focus on dark text
        gray = cv2.cvtColor(working_img, cv2.COLOR_BGR2GRAY)
        
        # Bilateral filter - preserves edges
        bilateral = cv2.bilateralFilter(gray, 9, 75, 75)
        preprocessed_images.append(("bilateral", bilateral))
        
        # Version 5: Otsu thresholding
        _, otsu = cv2.threshold(bilateral, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        preprocessed_images.append(("otsu", otsu))
        
        # Version 6: Inverted Otsu (for light text on dark background)
        _, otsu_inv = cv2.threshold(bilateral, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        preprocessed_images.append(("otsu_inverted", otsu_inv))
        
        # Version 7: Morphological operations to clean up
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2,2))
        morph = cv2.morphologyEx(otsu, cv2.MORPH_CLOSE, kernel)
        preprocessed_images.append(("morphological", morph))
        
        return preprocessed_images
    
    def is_valid_text(self, text):
        """Check if text is likely to be real readable text"""
        if not text or len(text. strip()) < 2:
            return False
        
        # Must have at least some letters
        if not re.search(r'[A-Za-z]', text):
            return False
        
        # Calculate ratio of alphanumeric to total
        alphanumeric = sum(c.isalnum() for c in text)
        total = len(text. replace(' ', ''))
        
        if total == 0:
            return False
        
        ratio = alphanumeric / total
        
        # At least 70% should be alphanumeric
        return ratio >= 0.7
    
    def extract_text_with_ocr(self, image_path):
        """Extract text using EasyOCR with multiple preprocessing strategies"""
        print(f"📸 Processing image: {image_path}")
        
        # Preprocess image with multiple strategies
        preprocessed_images = self.preprocess_image(image_path)
        
        all_results = []
        
        # Perform OCR on each preprocessed version
        print(f"🔍 Running AI text detection on {len(preprocessed_images)} image variants...")
        
        for idx, (strategy, img) in enumerate(preprocessed_images):
            print(f"  Processing variant {idx+1}/{len(preprocessed_images)}: {strategy}")
            try:
                # Use paragraph=False for better individual text detection
                results = self.reader.readtext(
                    img, 
                    paragraph=False,
                    text_threshold=0.6,  # Lower threshold for better detection
                    low_text=0.3
                )
                
                for (bbox, text, confidence) in results:
                    # Only keep valid text
                    if self.is_valid_text(text):
                        all_results.append({
                            'text': text. strip(),
                            'confidence':  confidence,
                            'bbox':  bbox,
                            'strategy': strategy,
                            'area': self.calculate_bbox_area(bbox)
                        })
            except Exception as e:
                print(f"    ⚠️ Error with {strategy}: {e}")
                continue
        
        # Remove duplicates and keep highest confidence
        unique_results = {}
        for item in all_results:
            # Normalize text for comparison
            text_normalized = item['text'].strip().upper()
            text_normalized = re.sub(r'\s+', ' ', text_normalized)  # Normalize spaces
            
            # Skip very short text
            if len(text_normalized) < 2:
                continue
            
            # Keep the result with highest confidence for each unique text
            if text_normalized not in unique_results or unique_results[text_normalized]['confidence'] < item['confidence']:
                unique_results[text_normalized] = item
        
        # Convert back to list and sort by position
        results_list = []
        for text_normalized, data in unique_results.items():
            y_pos = data['bbox'][0][1]  # Top-left Y coordinate
            x_pos = data['bbox'][0][0]  # Top-left X coordinate
            results_list.append({
                'text': data['text'],
                'confidence':  data['confidence'],
                'bbox': data['bbox'],
                'position': (y_pos, x_pos),
                'strategy': data['strategy'],
                'area': data['area']
            })
        
        # Sort by position (top to bottom, left to right)
        results_list.sort(key=lambda x: (x['position'][0], x['position'][1]))
        
        print(f"✅ Found {len(results_list)} unique text elements")
        
        return results_list
    
    def calculate_bbox_area(self, bbox):
        """Calculate area of bounding box"""
        points = np.array(bbox)
        x_coords = points[:, 0]
        y_coords = points[: , 1]
        width = max(x_coords) - min(x_coords)
        height = max(y_coords) - min(y_coords)
        return width * height
    
    def clean_medicine_name(self, text):
        """Clean up medicine name text"""
        # Remove excessive special characters
        cleaned = re.sub(r'[^\w\s\-/+()]', ' ', text)
        # Remove extra spaces
        cleaned = ' '.join(cleaned.split())
        # Remove standalone numbers at the start/end
        cleaned = re.sub(r'^\d+\s+', '', cleaned)
        cleaned = re.sub(r'\s+\d+$', '', cleaned)
        return cleaned.strip()
    
    def identify_medicine_name(self, extracted_data):
        """
        Intelligent medicine name identification using multiple heuristics
        """
        if not extracted_data:
            return []
        
        candidates = []
        
        # Common non-medicine keywords to filter out
        skip_patterns = [
            r'^MRP\s*: ?\s*\d+',
            r'BATCH\s*NO',
            r'MFG\s*DATE',
            r'EXP\s*DATE',
            r'NET\s*QTY',
            r'^\d+\s*ML$',
            r'^\d+\s*MG$',
            r'^\d+\s*TABLETS? $',
            r'^\d+\s*CAPSULES?$',
            r'^STRIP\s+OF',
            r'^BLISTER\s+OF',
            r'PVT\s*LTD',
            r'PHARMA(CEUTICALS? )?$',
            r'^IP\s*\d+',
            r'^\d+\s*X\s*\d+',
            r'^E\d+/\d+',  # Batch codes
            r'^\d{3,}/\d+',  # Codes like 772/22226123
            r'^[A-Z]\d+/\d+',  # Codes like R38/38628227
        ]
        
        # Medicine name indicators
        medicine_keywords = [
            'TABLETS', 'CAPS', 'CAPSULES', 'SYRUP', 'SUSPENSION', 'INJECTION',
            'HYDROCHLORIDE', 'SULPHATE', 'SULFATE', 'SODIUM', 'ACETATE',
            'MG', 'MCG', 'ML', 'IP', 'BP', 'USP'
        ]
        
        for idx, item in enumerate(extracted_data[: 25]):  # Check top 25 results
            text = item['text']. strip()
            text_upper = text.upper()
            confidence = item['confidence']
            position_score = 1.0 - (idx * 0.02)  # Slower decay
            area = item. get('area', 0)
            
            # Skip very short text
            if len(text) < 3:
                continue
            
            # Skip if only numbers
            if re.match(r'^\d+$', text):
                continue
            
            # Skip using patterns
            skip = False
            for pattern in skip_patterns:
                if re. search(pattern, text_upper):
                    skip = True
                    break
            
            if skip:
                continue
            
            # Skip if mostly special characters
            alpha_count = sum(c.isalpha() for c in text)
            if alpha_count < 3:
                continue
            
            # Calculate base score
            score = confidence * 0.35 + position_score * 0.25
            
            # Bonus:  Larger text (brand names are usually larger)
            if area > 0: 
                # Normalize area bonus (max 0.15)
                area_bonus = min(0.15, (area / 10000) * 0.05)
                score += area_bonus
            
            # Bonus:  Top 3 positions
            if idx < 3:
                score += 0.20
            
            # Bonus:  Title case or all caps with good length
            if (text. istitle() or text.isupper()) and 5 <= len(text) <= 30:
                score += 0.15
            
            # Bonus:  Contains letters and numbers (like "Prolee-10", "Crocin-650")
            if re.search(r'[A-Za-z]{4,}', text) and re.search(r'\d+', text):
                score += 0.20
            
            # Bonus:  Contains hyphen with letters on both sides
            if re.search(r'[A-Za-z]+-\d+', text):
                score += 0.15
            
            # Bonus: Good length
            if 5 <= len(text) <= 25:
                score += 0.10
            
            # Bonus: High confidence from original or deskewed
            if item. get('strategy') in ['original', 'deskewed'] and confidence > 0.75:
                score += 0.15
            
            # Bonus:  Contains medicine-related keywords
            if any(keyword in text_upper for keyword in medicine_keywords):
                # Small bonus, as these could be in descriptions too
                score += 0.05
            
            # Penalty:  Very long text (likely description)
            if len(text) > 40:
                score -= 0.20
            
            # Penalty:  Too many special characters
            special_count = sum(not c.isalnum() and not c.isspace() for c in text)
            if special_count > len(text) * 0.3:
                score -= 0.15
            
            # Penalty:  Starts with numbers (likely codes)
            if re.match(r'^\d', text):
                score -= 0.10
            
            # Clean the medicine name
            cleaned_name = self.clean_medicine_name(text)
            
            if not cleaned_name or len(cleaned_name) < 3:
                continue
            
            candidates.append({
                'name': cleaned_name,
                'original_text': text,
                'confidence': round(confidence * 100, 2),
                'score': round(score, 3),
                'position': idx + 1,
                'strategy': item. get('strategy', 'unknown'),
                'area': round(area, 2)
            })
        
        # Sort by score
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        # Filter out very low scoring candidates
        candidates = [c for c in candidates if c['score'] > 0.40]
        
        return candidates
    
    def process_image(self, image_path):
     """Main processing pipeline"""
    
    
     try:
        # Extract all text
        extracted_data = self.extract_text_with_ocr(image_path)
        
        if not extracted_data:
            return {
                'success': False,
                'error': 'No text detected in the image.  Please try a clearer image.'
            }
        
        # Identify medicine names
        medicine_candidates = self.identify_medicine_name(extracted_data)
        
        if not medicine_candidates:  
            return {
                'success': False,
                'error': 'Could not identify medicine name. Please try a different image or angle.'
            }
        
        # Get all extracted text for reference
        all_text = [
            {
                'text': str(item['text']),
                'confidence': float(round(item['confidence'] * 100, 2))
            }
            for item in extracted_data[: 30]  # Show top 30
        ]
        
        # Determine best match - convert all numpy types to Python types
        best_match = {
            'name': str(medicine_candidates[0]['name']),
            'confidence': float(medicine_candidates[0]['confidence']),
            'score': float(medicine_candidates[0]['score']),
            'position': int(medicine_candidates[0]['position']),
            'strategy': str(medicine_candidates[0]. get('strategy', 'unknown'))
        }
        
        # Convert all candidates
        all_candidates = []
        for c in medicine_candidates[: 10]: 
            all_candidates.append({
                'name': str(c['name']),
                'confidence':  float(c['confidence']),
                'score': float(c['score']),
                'position':  int(c['position']),
                'strategy': str(c. get('strategy', 'unknown'))
            })
        
        return {
            'success': True,
            'best_match': best_match,
            'all_candidates': all_candidates,
            'all_text': all_text,
            'total_text_found': len(all_text)
        }
        
     except Exception as e: 
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': f'Processing error: {str(e)}'
        }