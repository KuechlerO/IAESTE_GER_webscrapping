from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup # pip install beautifulsoup4

import pandas as pd

import os, sys

def dynamical_webscrapping_local():
    # Instantiate an Options object
    # and add the “ — headless” argument
    opts = Options()
    opts.add_argument("—headless")

    # If necessary set the path to you browser’s location
    # opts.binary_location = "/Applications/Google Chrome.app"

    # Set the location of the webdriver
    chrome_driver = os.getcwd() + "\chromedriver"
    chrome_driver = "/Users/oliverkuchler/PycharmProjects/iaeste_webScrapping/chromedriver"

    # Instantiate a webdriver
    driver = webdriver.Chrome(options=opts, executable_path=chrome_driver)
    # driver = webdriver.Chrome(executable_path=chrome_driver)

    # Load the HTML page
    #driver.get("/Users/oliverkuchler/PycharmProjects/iaeste_webScrapping/test.html", )
    #driver.get("file:/test.html")
    driver.get("file:///Users/oliverkuchler/PycharmProjects/iaeste_webScrapping/test.html")
    #driver.get("https://www.google.com")

    # To scrape a url rather than a local file
    # just do something like this
    # driver.get("https://your.url")

    # Put the page source into a variable and create a BS object from it
    soup_file = driver.page_source
    driver.quit()
    soup = BeautifulSoup(soup_file, "html.parser")# Load and print the title and the text of the <div>
    print(soup.title.get_text())
    print(soup.find(id="text").text.strip())


def dynamical_iaeste_webscrapping(email, password):
    print("Starting scrapping the IAESTE internship list")
    iaeste_login_url = "https://iaeste.smartsimple.ie/s_Login.jsp"
    chrome_driver = "/Users/oliverkuchler/PycharmProjects/iaeste_webScrapping/chromedriver"     # Chrome driver

    # Instantiate an Options object and add the “ — headless” argument
    opts = Options()
    opts.add_argument("—-headless")

    # Instantiate a webdriver
    driver = webdriver.Chrome(options=opts, executable_path=chrome_driver)
    driver.get(iaeste_login_url)

    driver.find_element_by_id('user').send_keys(email)
    driver.find_element_by_id('password').send_keys(password)
    driver.find_element_by_class_name('ButtonSm').click()
    driver.implicitly_wait(10)

    # Check if account data is correct by randomly checking for iframes
    try:
        driver.find_elements_by_tag_name("iframe")[9]  # test if log-in was successfull
    except Exception as e:
        print("Error '", e, "' was thrown. Maybe your account data is incorrect.")
        print("Unexpected error:", sys.exc_info()[0])
        driver.quit()
        raise e

    not_reached_end = True      # have we gone through all list entries?
    all_entries_list = []
    while not_reached_end:
        print("Still scrapping!")
        driver.switch_to.frame(driver.find_elements_by_tag_name("iframe")[9])   # load iframe
        driver.switch_to.frame(driver.find_element_by_tag_name("iframe"))   # load sub-iframe

        soup_file = driver.page_source
        all_entries_list.extend(scrap_available_offers_table(driver))       # load current entries

        # ------- Click on next-button if not reached end yet -------------
        soup = BeautifulSoup(soup_file, "html.parser")
        counter_on_page = soup.find("div", {"id": "pagedisplay"}).text.strip().split(" ")
        if int(counter_on_page[0].split("-")[1]) < int(counter_on_page[2]):
            next_button = driver.find_element_by_css_selector("a[class='btn btn-default next lastvisible']")
            driver.execute_script("arguments[0].click();", next_button)     # Use JS to perform click
            driver.switch_to.default_content()  # switch back to default
        else:
            not_reached_end = False

    driver.quit()
    return all_entries_list


def scrap_available_offers_table(driver):
    """
    Scraps the currently displayed table entries
    :param driver:  The driver with focus on the iframe-table
    :return:    List of row-entries
    """
    driver.find_elements_by_tag_name("tbody")  # makes sure that everything is loaded
    soup_file = driver.page_source
    soup = BeautifulSoup(soup_file, "html.parser")
    table_body = soup.find("tbody")
    rows = table_body.find_all("tr")

    # Capture the content of each row
    all_rows_content_list = []
    for row in rows:
        current_row_content = []
        row_entries = row.find_all("td")[:-2]
        for entry in row_entries:
            current_row_content.append(entry.text.strip())
        all_rows_content_list.append(current_row_content)

    return all_rows_content_list


def setting_up_csv_file(all_rows_content_list):
    # Create the pandas DataFrame
    data = []
    for entry in all_rows_content_list:
        if entry[0] is not "":      # catch empty entries
            # Not Remote, at least 8 weaks, and IT
            if "REMOTE" not in entry[2] and int(entry[5].split(" to ")[1]) >= 8 \
                    and "11-COMPUTER AND INFORMATION SCIENCES" in entry[4]:
                data.append(entry)
            else:
                continue

    df = pd.DataFrame(data, columns=["ID", "Ref-Nr.", "Offer Type", "Committee", "General Discipline",
                                     "No. of Weeks", "Period of training", "Completed Years of study", "Date published",
                                     "Deadline for nomination", "Exchange Type"])
    df.to_csv("relevant_internship_positions.csv")


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    if len(sys.argv) <= 2:
        print("Error: Arguments missing...")
        print("Remember to pass your IAESTE-Account data as arguments to the script!")
        print("1. Argument: Email -> E.g. Oli@web.de")
        print("2. Argument: Password -> E.g. superstrong_password")
    else:
        print('Argument List:', str(sys.argv))
        email = sys.argv[1]
        password = sys.argv[2]
        all_entries = dynamical_iaeste_webscrapping(email, password)
        setting_up_csv_file(all_entries)