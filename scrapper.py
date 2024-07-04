from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from time import sleep
import requests
import pandas as pd
from time import sleep
import datetime
import time


# Function to scrape data from a specific page using BeautifulSoup
def scrape_data_from_page(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', {'class': 'data-table text-nowrap striped mark-visited'})

        if table:
            data = []
            rows = table.find_all('tr')
            for row in rows[1:]:
                cells = row.find_all('td')
                row_data = [cell.text.strip() for cell in cells]
                data.append(row_data)

            return data
        else:
            print(f"No table found on {url}")
            return None
    else:
        print(f"Failed to retrieve {url}. Status code: {response.status_code}")
        return None

# Function to get all page URLs for pagination
def get_all_page_urls(base_url):
    page_urls = [base_url]
    page_num = 1  # Start with page 2

    # while base_url:
    url = f"{base_url}?page={page_num}"
    
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        next_div = soup.find('div', {'class': 'flex-baseline options'})
        try:
            alist = [link.text.strip() for link in next_div.find_all('a') if next_div]
            # print("alist", len(alist), alist)

            for page_num in range(2, len(alist)):
                url = f"{base_url}?page={page_num}"
                page_urls.append(url)

        except:
            print("No next page")      
    return page_urls


# Function to scrape all pages and save data into a single CSV file
def scrape_and_save_data(base_url, company_name):
    page_urls = get_all_page_urls(base_url)
    all_data = []

    print(f"company_name : {company_name} \npage_urls : {page_urls}")
    for url in page_urls:
        data = scrape_data_from_page(url)
        if data:
            all_data.extend(data)
        sleep(1)  # Add a delay to be polite to the server

    header_names = ['S.No.', 'Name', 'CMP(Rs)', 'P/E', 'Mar Cap(Rs.Cr)', 'Div Yld(%)',
                    'NP Qtr(Rs.Cr)', 'Qtr Profit Var(%)', 'Sales Qtr(Rs.Cr.)',
                    'Qtr Sales Var(%)', 'ROCE(%)']
    
    cleaned_company_name = ''.join(letter for letter in company_name if letter.isalnum())
    csv_filename = f"data\{cleaned_company_name}.csv"
    
    df = pd.DataFrame(all_data, columns=header_names)
    df['Company Name'] = company_name
    df.dropna(subset=['S.No.'], inplace=True)  # Drop rows where 'S.No' is NaN
    df.to_csv(csv_filename, index=False)

    print(f"Data saved to {csv_filename} \n")

def scrape_companies(base_url, email, password):
    """
    Function to scrape company names and URLs from the specified base URL.
    """
    options = Options()
    options.add_argument("--headless")  # Uncomment this line to run in headless mode
    options.add_argument("--window-size=1920x1080")
    driver = webdriver.Chrome(options=options)

    try:
        # Open the website
        driver.get(base_url)

        # Wait until login button is clickable
        login_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "/html/body/nav/div[2]/div/div/div/div[2]/div[2]/a[1]/i")))
        login_button.click()

        # Enter email and password
        email_field = driver.find_element(By.ID, "id_username")
        email_field.send_keys(email)

        password_field = driver.find_element(By.ID, "id_password")
        password_field.send_keys(password)

        # Submit login form
        submit_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        submit_button.click()

        # Wait for login to complete (adjust sleep time as needed)
        time.sleep(5)

        response = requests.get(base_url)
        company_names = []
        final_urls = []

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            explore_link = soup.find('a', href='/explore/')
            
            if explore_link:
                explore_url = base_url + explore_link.get('href')
                response_explore = requests.get(explore_url)
                
                if response_explore.status_code == 200:
                    soup_explore = BeautifulSoup(response_explore.content, 'html.parser')
                    all_links = soup_explore.find_all('a', class_='bordered radius-6 padding-4-12 font-size-14 ink-700')
                    
                    for link in all_links:
                        company_names.append(link.text.strip())
                        final_urls.append(base_url + link.get('href'))
                        
                    return company_names, final_urls  # Return after scraping initial page
                else:
                    print(f"Failed to retrieve {explore_url}. Status code: {response_explore.status_code}")
            else:
                print(f"'/explore/' link not found on {base_url}")
        else:
            print(f"Failed to retrieve {base_url}. Status code: {response.status_code}")

        return [], []  # Return empty lists if scraping fails
    except Exception as e:
        print(f"Error: {e}")

    finally:
        # Close the browser session
        driver.quit()


# Main function
def main():
    start_time = datetime.datetime.now()

    base_url = 'https://www.screener.in/'
    email = 'venkataraok766@gmail.com'
    password = 'Busarapalli@399'

    company_names, final_urls = scrape_companies(base_url, email, password)
    
    if company_names and final_urls:
        for url, name in zip(final_urls, company_names):
            scrape_and_save_data(url, name)
    end_time = datetime.datetime.now()
    diff_time = end_time-start_time
    print(f"start time: {start_time}, end time: {end_time} and diff time: {diff_time}")
    print("Data scraping and CSV creation completed!!.")

if __name__ == '__main__':
    main()