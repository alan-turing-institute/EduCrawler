"""
EduHub portal crawling module.
"""

from time import sleep

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from webdriver_manager.chrome import ChromeDriverManager

from educrawler.utilities import log

from educrawler.constants import (
    CONST_PORTAL_ADDRESS,
    CONST_REFRESH_SLEEP_TIME,
    CONST_MAX_REFRESH_COUNT,
    CONST_SLEEP_TIME,
    CONST_MFA_SLEEP_TIME,
    CONST_PORTAL_COURSES_ADDRESS,
    CONST_DEFAULT_LAB_NAME
)

class Crawler:
    """
    Class responsible for crawling the EduHub portal.

    """

    def __init__(self, login_email, login_pass, hide=True, mfa=True):
        """
        Creates a cleint and logins to the EduHub portal. 

        Arguments:
            login_email - login email
            login_pass - login password
            hide - hide chromium while the action are taken
            mfa - does login involve mfa, if so wait some more time for it.

        Returns:
            client - webdriver client if login was successful, otherwise None
        """

        options = Options()

        if hide:
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

        self.client = webdriver.Chrome(ChromeDriverManager().install(), options=options)

        self.client.get(CONST_PORTAL_ADDRESS)

        # entering email address
        self.client.find_element_by_xpath("//input[@type='email']").send_keys(login_email)
        self.client.find_element_by_xpath("//input[@type='submit']").click()

        sleep(CONST_SLEEP_TIME)

        # entering password
        self.client.find_element_by_xpath("//input[@name='passwd']").send_keys(login_pass)
        self.client.find_element_by_xpath("//input[@type='submit']").click()

        sleep(CONST_SLEEP_TIME)

        # wait until the mfa has been approved
        if mfa:
            sleep_counter = 0
            sleep_wait = True

            while sleep_wait and sleep_counter < CONST_MAX_REFRESH_COUNT:
                log("Sleeping while waiting for MFA approval (%f).." % (CONST_REFRESH_SLEEP_TIME), indent=2)
                sleep(CONST_REFRESH_SLEEP_TIME)

                try:
                    element = self.client.find_element_by_id("idDiv_SAOTCAS_Title")
                except:
                    try:
                        self.client.find_element_by_xpath("//input[@type='submit']")
                        log("Approved!", indent=2)
                        sleep_wait = False
                    except:
                        sleep_wait = True
                
                sleep_counter += 1 

            if sleep_wait == True:
                log("MFA was not approved! Quiting.")
                
                self.client.quit()
                self.client = None
            else:
                self.client.find_element_by_xpath("//input[@type='submit']").click()
                sleep(CONST_SLEEP_TIME)


    def get_courses(self):
        """
        Loads courses page

        """

        log("Getting the list of courses")

        log("Loading %s" % (CONST_PORTAL_COURSES_ADDRESS), indent=2)
        self.client.get(CONST_PORTAL_COURSES_ADDRESS)
        
        # Finds table entries
        log("Finding courses", indent=2)

        sleep_counter = 0
        sleep_wait = True

        while sleep_wait and sleep_counter < CONST_MAX_REFRESH_COUNT:

            log("Sleeping while courses are loading (%f).." % (CONST_REFRESH_SLEEP_TIME), indent=2)
            sleep(CONST_REFRESH_SLEEP_TIME)

            entries = self.client.find_elements_by_xpath('//*[@class="fxs-portal-hover fxs-portal-focus azc-grid-row"]')

            if len(entries) != 0:
                sleep_wait = False
                log("Loaded!", indent=2)
        
        return entries


    def get_courses_df(self):
        """
        Gets the list of courses as pandas dataframe.

        """

        entries = self.get_courses()
        
        data = []

        for entry in entries:
            elements = entry.find_elements_by_class_name("azc-grid-cellContent")

            course_name = None
            course_budget = None
            course_usage = None
            course_students = None
            course_project_groups = None

            for index, element in enumerate(elements): 
                if index == 0:
                    course_name = element.text
                elif index == 1:
                    course_budget = element.text
                elif index == 2:
                    course_usage = element.text
                elif index == 3:
                    course_students = element.text
                elif index == 4:
                    course_project_groups = element.text

            if course_name is not None:
                data.append([course_name, course_budget, course_usage, course_students, course_project_groups]) 

        courses_df = pd.DataFrame(data, columns = ['Name', 'Assigned credit', 'Consumed', 'Students', 'Project groups'])

        log("Found %d courses!" % (len(courses_df.index)), indent=2)

        print(courses_df)

        return courses_df
   

    def get_course_details(self, course_name):
        """
        Gets the details about the course, such us total consumption, list of 
            subscriptions and their usage.

        Arguments:
            course_name: name of the course
        """

        found = False
        log("Looking for %s details" % (course_name))

        # first navigate to the courses page and wait till it loads
        entries = self.get_courses()

        # select 
        for entry in entries:
            elements = entry.find_elements_by_class_name("azc-grid-cellContent")

            if elements[0].text == course_name:
                log("Found %s!" % (course_name), indent=2)
                found = True
                break
        
        if not found:
            log("Could not find %s course. Returning." % (course_name), indent=2)
            return None

        elements[0].click()
        
        # load
        log("Opening %s" % (course_name), indent=2)

        sleep_counter = 0
        sleep_wait = True
        found = False

        while sleep_wait and sleep_counter < CONST_MAX_REFRESH_COUNT:

            log("Sleeping while the course is loading (%f).." % (CONST_REFRESH_SLEEP_TIME), indent=2)
            sleep(CONST_REFRESH_SLEEP_TIME)

            entries = self.client.find_elements_by_xpath('//*[@class="azc-grid-groupdata"]')

            if len(entries) != 0:
                sleep_wait = False
                log("Loaded!", indent=2)
                found = True
        
        if not found:
            log("Could not load %s course. Returning." % (course_name), indent=2)
            return None

        # wait until the overview page is loaded
        sleep_counter = 0
        sleep_wait = True
        found = False
        course_title = None

        while sleep_wait and sleep_counter < CONST_MAX_REFRESH_COUNT:

            log("Sleeping while the course overview is loading (%f).." % (CONST_REFRESH_SLEEP_TIME), indent=2)
            sleep(CONST_REFRESH_SLEEP_TIME)

            course_title_list = self.client.find_elements_by_class_name("ext-classroom-overview-class-name-title")

            if len(course_title_list) != 0:
                sleep_wait = False
                log("Loaded!", indent=2)
                found = True
                course_title = course_title_list[0].text

        if not found:
            log("Could not load %s course. Returning." % (course_name), indent=2)
            return None

        if course_title != course_name:
            log("The loaded course's title (%s) doesn't match the given name (%s)." % (course_title, course_name), indent=2)
            return None

        ################################################################################################
        # course overview -> "project" lab
        ################################################################################################

        found = False

        classroom_grid = self.client.find_element_by_class_name("ext-classroom-overview-assignment-grid")
        
        entries = classroom_grid.find_elements_by_class_name("azc-grid-groupdata")

        for entry in entries:

            element = entry.find_element_by_class_name("ext-grid-clickable-link")

            if element.text.lower() == CONST_DEFAULT_LAB_NAME.lower():
                log("Found %s lab!" % (CONST_DEFAULT_LAB_NAME), indent=2)
                found = True
                break
        
        if not found:
            log("Could not find %s lab. Returning." % (CONST_DEFAULT_LAB_NAME), indent=2)
            return None

        else:
            element.click()

        ################################################################################################
        # "project" lab -> "more"
        ################################################################################################

        # sleep(4)

        # found = False

        # try:
        #     more_buttom = self.client.find_element_by_class_name("ext-assignment-detail-more-handout-link")
        #     found = True
        # except:
        #     found = False
        
        # print("more_buttom: ", more_buttom)
        # #more_buttom.click()

        
        sleep(30)
            

    def quit(self):
        """
        Nicely turns off the crawler.

        """

        if self.client is not None:

            self.client.quit()

            self.client = None

