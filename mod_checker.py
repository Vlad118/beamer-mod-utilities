import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def read_last_update_date(last_update_file):
    last_update_date = datetime(2010, 4, 1)    # Default date if above file does not exist or error
    vlad_date = datetime(2010, 4, 1)           # Default Vlad date

    if os.path.exists(last_update_file):
        with open(last_update_file, "r") as file:
            last_update_date_str = file.readline().strip()
            vlad_date_str = file.readline().strip()
            try:
                 last_update_date = datetime.strptime(last_update_date_str, "%Y-%m-%d")
                 vlad_date = datetime.strptime(vlad_date_str, "%Y-%m-%d")
            except ValueError:
                print("Invalid date format in last_update.txt. Resetting to default.")
    
    return last_update_date, vlad_date

def get_mod_last_update_date(mod_url):
    try:
        # Mimic browser header
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        response = requests.get(mod_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Get and format date of last update
        last_update_container = soup.find('dl', class_='lastUpdate')
        last_updated_element = last_update_container.find('span', class_='DateTime')
        
        if last_updated_element:    # date in span tag
            last_update_date_str = last_updated_element.text.strip()
        else:                       # date in abbr tag
            last_updated_element = last_update_container.find('abbr', class_='DateTime')
            last_update_date_str = last_updated_element['data-datestring'].strip()

        last_update_date = datetime.strptime(last_update_date_str, '%b %d, %Y')
        return last_update_date

    except Exception as e:
        print(f"Error fetching mod info for {mod_url}: {e}")
        return None

def get_mods_needing_update(mods, mods_needing_update, vlad_update_list, last_update_date, vlad_date):
    total_mods = len(mods)

    for i, mod_url in enumerate(mods):
        mod_url = mod_url.strip()
        mod_last_update_date = get_mod_last_update_date(mod_url)

        # Display progress bar during the update check
        printProgressBar(i + 1, total_mods, prefix='Checking Mods:', suffix='Complete', length = 30)

        if mod_last_update_date:
            if mod_last_update_date > last_update_date:
                print(f"{mod_url} requires an update.")
                mods_needing_update.append(mod_url)

                if mod_last_update_date > vlad_date:
                    vlad_update_list.append(mod_url)

def update_mods(mods_needing_update, vlad_update_list, vlad_date, download_dir, last_update_file):
    if mods_needing_update:
        update_choice = input("\nDo you want to update beamer mods? (y/n): ").lower()
        if update_choice == 'y':

            # Progress bar stuff
            l = len(mods_needing_update)
            i = 0
            print("")
            
            for mod_url in mods_needing_update:
                mod_name = mod_url.split('/')[-2].ljust(40)[:40]

                printProgressBar(i, l, prefix = 'Progress:', suffix = f"Downloading {mod_name}", length = 30)
                download_mod(mod_url, mod_name, download_dir)  # Assuming mod name is in URL

                # Update Progress Bar
                i += 1

            printProgressBar(1, 1, prefix = 'Progress:', suffix = f"Completed".ljust(50), length = 30)

            if vlad_update_list:
                print("\nSend to Vlad:")
                for mod in vlad_update_list:
                    print(mod)

            with open(last_update_file, "w") as file:
                file.write(datetime.now().strftime("%Y-%m-%d") + "\n")
                file.write(vlad_date.strftime("%Y-%m-%d"))
        else:
            print("Ok man")
            return
    else:
        print("All mods up to date")

def download_mod(mod_url, mod_name, download_dir):
    # Configure Selenium options
    options = webdriver.ChromeOptions()
    
    options.add_experimental_option("excludeSwitches", ['enable-logging'])
    options.set_capability("browserVersion", "117")

    options.add_argument("--log-level=3")  # Suppress logs for headless mode
    options.add_argument('--headless')     # Run Chrome in headless mode
    prefs = {"download.default_directory": download_dir}
    options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(options=options)

    try:
        # Open the mod URL
        driver.get(mod_url)

        # Find download button and click it     (FOR NON-HEADLESS)
        # download_button = WebDriverWait(driver, 10).until(
        #     EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Download')]"))
        # )
        # download_button.click()

        # Execute JavaScript to click the download button directly  (FOR HEADLESS BROWSER)
        download_button_script = """
        const downloadButton = document.querySelector('a[href*="download"]');
        if (downloadButton) {
            downloadButton.click();
        }
        """
        driver.execute_script(download_button_script)

        # print(f"Downloading {mod_name} from {mod_url}")

        # Wait for download to complete
        zip_files = [f for f in os.listdir(download_dir) if f.endswith(".zip")]
        initial_zips = len(zip_files)
        start_time = time.time()
        while True:
            time.sleep(1)
            # Count number of zip files in download directory
            zip_files = [f for f in os.listdir(download_dir) if f.endswith(".zip")]
            if len(zip_files) > initial_zips:
                break
            if time.time() - start_time > 1200:  # Timeout after 20 minutes
                raise TimeoutError("Download timeout exceeded.")
    except Exception as e:
        print(f"Error downloading mod {mod_name} from {mod_url}: {e}")
    finally:
        driver.quit()

# Print iterations progress
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()

def main():
    download_dir = "D:\downloaded"          # Mod download directory
    mods_file = "mods.txt"                  # File containing list of mod URLs
    last_update_file = "last_update.txt"    # File containing date of last successful update

    last_update_date, vlad_date = read_last_update_date(last_update_file)

    if not os.path.exists(mods_file):
        print(f"The file {mods_file} does not exist.")
        return

    with open(mods_file, "r") as file:
        mods = file.readlines()

    mods_needing_update = []
    vlad_update_list = []

    get_mods_needing_update(mods, mods_needing_update, vlad_update_list, last_update_date, vlad_date)

    update_mods(mods_needing_update, vlad_update_list, vlad_date, download_dir, last_update_file)

if __name__ == "__main__":
    main()