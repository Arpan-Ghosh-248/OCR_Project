from django.shortcuts import render
from django.http import JsonResponse
from .models import VisitingCard
from .forms import CardUploadForm
from django.views.decorators.csrf import csrf_exempt
import pytesseract
from PIL import Image
import re
import ipdb
# Create your views here.

def perform_ocr(image_path):
    # Perform OCR using Tesseract
    text = pytesseract.image_to_string(Image.open(image_path))
    # ipdb.set_trace()
    return text


def extract_info_from_text(text):
    # Regular expressions for different data types
    email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    phone_regex = r'(\+?\d{1,2}\s?)?(\(?\d{3}\)?[\s.-]?)?\d{3}[\s.-]?\d{4}'
    url_regex = r'(https?://[^\s]+)|(www\.[^\s]+)'
    job_title_regex = r'\b(Manager|Engineer|Developer|Designer|Director|Coordinator|Analyst|Consultant|Specialist|Executive|Administrator|Technician)\b'

    
    # Extract email address
    email_match = re.search(email_regex, text)
    email = email_match.group() if email_match else None

    # Extract phone number
    phone_match = re.search(phone_regex, text)
    phone_number = phone_match.group() if phone_match else None

    # Extract website URL
    url_match = re.search(url_regex, text)
    website = url_match.group() if url_match else None

    # Extract job title using regex
    job_title = None
    job_title_matches = re.finditer(job_title_regex, text, re.IGNORECASE)
    for match in job_title_matches:
        # Capture the complete line containing the job title
        start_pos = text.rfind('\n', 0, match.start())
        end_pos = text.find('\n', match.end())
        start_pos = start_pos if start_pos != -1 else 0
        end_pos = end_pos if end_pos != -1 else len(text)
        job_title_text = text[start_pos:end_pos].strip()
        job_title = job_title_text
        break 

    # Extract name from the first non-matching line or lines with specific patterns
    lines = text.splitlines()
    name = None
    for line in lines:
        if line.strip() and all(not re.search(regex, line) for regex in [email_regex, phone_regex, url_regex]):
            name = line.strip()
            break

    # Extract address
    address_lines = []
    address_keywords = ['Street', 'Ave', 'Avenue', 'Rd', 'Road', 'Blvd', 'Boulevard', 'Suite', 'Unit']
    for line in lines:
        if any(keyword in line for keyword in address_keywords) or any(char.isdigit() for char in line):
            address_lines.append(line.strip())

    address = " ".join(address_lines).strip() if address_lines else None

    # Extract company name
    company_name = None
    company_keywords = ['Company', 'Corp', 'Corporation', 'Ltd', 'Limited', 'Inc', 'Incorporated', 'LLC']
    for line in lines:
        if any(keyword in line for keyword in company_keywords):
            company_name = line.strip()
            break

    # Creating a dictionary of extracted information
    extracted_info = {
        "name": name,
        "job_title": job_title,
        "company_name": company_name,
        "email": email,
        "phone_number": phone_number,
        "address": address,
        "website": website
    }
    
    return extracted_info

def upload_card(request):
    # ipdb.set_trace()
    extracted_info = None
    if request.method == 'POST':
        form = CardUploadForm(request.POST, request.FILES)
        if form.is_valid():
            card = form.save()
            # Perform OCR on the uploaded image
            image_path = card.image.path
            extracted_text = perform_ocr(image_path)

            # Extract information from the extracted text
            extracted_info = extract_info_from_text(extracted_text)

            # Update the card instance with the extracted information
            card.name = extracted_info.get('name')
            card.job_title = extracted_info.get('job_title')
            card.company_name = extracted_info.get('company_name')
            card.email = extracted_info.get('email')
            card.phone_number = extracted_info.get('phone_number')
            card.address = extracted_info.get('address')
            card.save()

            # return JsonResponse({'message': 'Card uploaded and processed successfully!', 'data': extracted_info}, status=200)
    else:
        form = CardUploadForm()
    
    return render(request, 'cards/upload_card.html', context={'form': form, 'extracted_info': extracted_info})



