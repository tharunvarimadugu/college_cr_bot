import requests
from bs4 import BeautifulSoup
import logging
from urllib.parse import urljoin

# Set up a logger for this module
logger = logging.getLogger(__name__)

class result_bot:
    
    def __init__(self):
        """Initializes the bot."""
        self.departments = {}
        self.valid = []

    def bot_work(self, all_data_collected):
        """
        Fetches the result link and scrapes the list of departments using requests.
        all_data_collected[0] = result link
        """
        try:
            url = all_data_collected[0]
            logger.info(f"Fetching URL: {url}")
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            select_department = soup.find('select', id='department1')
            if not select_department:
                logger.error("Could not find department select box.")
                return []
                
            options = select_department.find_all('option')
            
            # Populate instance variables
            self.departments = {opt.text.strip(): opt.get("value") for opt in options}
            # Remove placeholder if exists (usually has empty value or specific text)
            self.departments = {k: v for k, v in self.departments.items() if v and "Select Department" not in k}
            
            self.valid = list(self.departments.keys())
            
            logger.info(f"Successfully fetched {len(self.valid)} departments.")
            return self.valid
            
        except Exception as e:
            logger.error(f"Error in bot_work: {e}", exc_info=True)
            return []

    def select_department(self, all_data_collected):
        """
        Submits the form with all details using requests and returns the result as text.
        all_data_collected = [link, department_index, roll, dob]
        """
        try:
            link = all_data_collected[0]
            department_index = all_data_collected[1]
            roll_number = all_data_collected[2]
            date_of_birth = all_data_collected[3]
            
            # Get department value
            if 0 <= department_index < len(self.valid):
                choice = self.valid[department_index]
                value = self.departments.get(choice)
            else:
                return "Error: Invalid department selection."

            logger.info(f"Submitting for: {choice} ({value}), Roll: {roll_number}, DOB: {date_of_birth}")

            # Prepare form data
            # Based on previous analysis: department1, usn, dateofbirth
            payload = {
                'department1': value,
                'usn': roll_number,
                'dateofbirth': date_of_birth
            }
            
            # Submit POST request
            # The form action is usually the same URL or relative. 
            # We'll post to the same URL as 'link' since the action was 'myresultug?resultid=...' which matches the link.
            response = requests.post(link, data=payload, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Find the result table
            # The original code looked for the 2nd table.
            tables = soup.find_all('table')
            
            # Find the result table
            # The structure is:
            # Table 0: Search form
            # Table 1: Result data (nested with headers directly in table tag sometimes)
            # Table 2: Footer
            
            tables = soup.find_all('table')
            result_table = None
            
            # Heuristic: Look for a table containing "Roll Number" or "Course Code"
            for table in tables:
                text = table.get_text()
                if "Roll Number" in text and "Course Code" in text:
                    result_table = table
                    break
            
            if result_table:
                # Extract Student Info
                text_content = result_table.get_text(" ", strip=True)
                
                # Simple extraction using string splitting if structure is consistent
                # Or better, iterate rows.
                
                rows = result_table.find_all('tr')
                
                student_info = []
                marks_data = []
                gpa_data = []
                
                mode = "info" # info, marks, gpa
                
                for row in rows:
                    cols = row.find_all(['th', 'td'])
                    cols_text = [ele.get_text(strip=True) for ele in cols]
                    
                    if not cols_text:
                        continue
                        
                    line_text = " ".join(cols_text)
                    
                    if "Roll Number:" in line_text:
                         student_info.append(f"**{line_text}**")
                    elif "Name:" in line_text:
                         student_info.append(f"**{line_text}**")
                    elif "Course Code" in line_text:
                        mode = "marks"
                        marks_data.append("| Code | Course Name | Credits | Grade | GP |")
                        marks_data.append("|---|---|---|---|---|")
                    elif "Credits Taken" in line_text:
                        mode = "gpa"
                        gpa_data.append("| Credits Taken | Earned | SGPA | CGPA | Total |")
                        gpa_data.append("|---|---|---|---|---|")
                    else:
                        # Data rows
                        if mode == "marks":
                            # Ensure we have enough columns for a valid marks row
                            # Expected: Code, Name (colspan 2?), Credits, Grade, GP
                            # HTML structure might vary, but let's try to format it.
                            if len(cols_text) >= 5:
                                marks_data.append(f"| {' | '.join(cols_text)} |")
                        elif mode == "gpa":
                            gpa_data.append(f"| {' | '.join(cols_text)} |")

                # Construct final message
                message_parts = []
                if student_info:
                    message_parts.extend(student_info)
                    message_parts.append("") # Spacer
                
                if marks_data:
                    message_parts.append("**Results:**")
                    message_parts.extend(marks_data)
                    message_parts.append("")
                    
                if gpa_data:
                    message_parts.append("**GPA:**")
                    message_parts.extend(gpa_data)
                
                if not message_parts:
                     # Fallback if parsing failed but table was found
                     return f"Found result but could not parse details.\nRaw text: {text_content[:500]}"
                     
                return "\n".join(message_parts)

            else:
                # Check for error messages in the whole page text
                page_text = soup.get_text()
                if "Date of Birth is Wrong" in page_text:
                     return "Error: Date of Birth is incorrect."
                if "Invalid" in page_text or "not found" in page_text:
                     return "Error: Invalid details or no result found."
                
                logger.warning("Could not find the result table in response.")
                return "Error: Could not find result table."

        except Exception as e:
            logger.error(f"Error in select_department: {e}", exc_info=True)
            return f"An error occurred: {e}"

if __name__ == "__main__":
    pass
