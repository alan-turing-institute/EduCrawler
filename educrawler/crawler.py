"""
EduHub portal crawling module.
"""

from datetime import datetime
from time import sleep
import pandas as pd
import logging

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

        log("Logging to %s as %s" % (CONST_PORTAL_ADDRESS, login_email), level=1)

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
            log("Waiting for MFA approval.", level=1)

            sleep_counter = 0
            sleep_wait = True

            while sleep_wait and sleep_counter < CONST_MAX_REFRESH_COUNT:
                log("Sleeping (%f).." % (CONST_REFRESH_SLEEP_TIME), level=3, indent=2)
                sleep(CONST_REFRESH_SLEEP_TIME)

                try:
                    element = self.client.find_element_by_id("idDiv_SAOTCAS_Title")
                except:
                    try:
                        self.client.find_element_by_xpath("//input[@type='submit']")
                        log("MFA approved!", level=1)
                        sleep_wait = False
                    except:
                        sleep_wait = True
                
                sleep_counter += 1 

            if sleep_wait == True:
                log("MFA was not approved! Stopping.", level=0)
                
                self.client.quit()
                self.client = None
            else:
                self.client.find_element_by_xpath("//input[@type='submit']").click()
                sleep(CONST_SLEEP_TIME)


    def get_courses(self):
        """
        Loads courses page

        """

        log("Getting the list of courses", level=1)

        log("Loading %s" % (CONST_PORTAL_COURSES_ADDRESS), level=2, indent=2)
        self.client.get(CONST_PORTAL_COURSES_ADDRESS)
        
        # Finds table entries
        sleep_counter = 0
        sleep_wait = True

        while sleep_wait and sleep_counter < CONST_MAX_REFRESH_COUNT:

            log("Sleeping while courses are loading (%f).." % (CONST_REFRESH_SLEEP_TIME), level=3, indent=2)
            sleep(CONST_REFRESH_SLEEP_TIME)

            entries = self.client.find_elements_by_xpath('//*[@class="fxs-portal-hover fxs-portal-focus azc-grid-row"]')

            if len(entries) != 0:
                sleep_wait = False
                log("List of courses loaded!", level=2, indent=2)
        
        log("Found %d courses." % (len(entries)), level=1, indent=2)

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

        return courses_df
   

    def get_course_details_df(self, course_name):
        """
        Gets the details about the course, such us total consumption, list of 
            subscriptions and their usage.

        Arguments:
            course_name: name of the course
        Returns:
            details_df: pandas dataframe containing all the course's handouts and their details
            error: error message if an error was encountered
        """

        details_df = None

        error = None
        found = False
        log("Looking for %s course details" % (course_name), level=1)

        ############################################################################
        # first navigate to the courses page and wait till it loads
        ############################################################################

        entries = self.get_courses()

        ############################################################################
        # select the course
        ############################################################################
        
        for entry in entries:
            elements = entry.find_elements_by_class_name("azc-grid-cellContent")

            if elements[0].text == course_name:
                log("(%s) course found." % (course_name), level=1)
                found = True
                break
        
        if not found:
            error = "Could not find (%s) course. Returning." % (course_name)
            log(error, level=0)
            return None, error

        ############################################################################
        # wait until the course overview page is loaded
        ############################################################################

        elements[0].click()

        log("Loading (%s) course " % (course_name), level=1)

        sleep_counter = 0
        found = False
        course_title = None

        while not found and sleep_counter < CONST_MAX_REFRESH_COUNT:

            log("Sleeping while the (%s) course overview is loading (%f).." % (course_name, CONST_REFRESH_SLEEP_TIME), level=3, indent=2)
            sleep(CONST_REFRESH_SLEEP_TIME)

            course_title_list = self.client.find_elements_by_class_name("ext-classroom-overview-class-name-title")

            if len(course_title_list) != 0:
                log("(%s) course overview loaded." % (course_name), level=2)
                found = True
                course_title = course_title_list[0].text

        if not found:
            error = "Could not load (%s) course. Returning." % (course_name)
            log(error, level=0, indent=2)
            return None, error

        if course_title != course_name:
            error = "The loaded course's title (%s) doesn't match the given name (%s)." % (course_title, course_name)
            log(error, level=0, indent=2)
            return None, error

        ############################################################################
        # finding all the labs that belong to the course and getting their details
        ############################################################################

        classroom_grid = self.client.find_element_by_class_name("ext-classroom-overview-assignment-grid")
        
        entries = classroom_grid.find_elements_by_class_name("ext-grid-clickable-link")

        log("(%s) course has %d lab(s)." % (course_name, len(entries)), level=1)

        for element in entries:
            
            lab_name = element.text.lower()

            log("Loading (%s) course -> (%s) lab blade." % (course_name, lab_name), level=1)

            element.click()

            handouts_df, error = self.get_lab_details(course_name, lab_name)
            
            if error is not None:
                break
            
            if details_df is None:
                details_df = handouts_df
            else:
                details_df = details_df.append(handouts_df)

        if error is None:
            return details_df, error
        else:
            return None, error
     

    def get_lab_details(self, course_name, lab_name):
        """
        Gets the details (handouts' details) of a selected lab.

        Arguments:
            course_name: the name of the course
            lab_name: the name of the lab

        Returns:
            handouts_df: pandas dataframe
        """

        log("Loading (%s) course -> (%s) lab -> more blade." % (course_name, lab_name), \
            level=1)

        sleep_counter = 0
        found = False
        more_buttom = None

        while not found and sleep_counter < CONST_MAX_REFRESH_COUNT:

            log("Sleeping while the initial handout list is loading (%f).." % (CONST_REFRESH_SLEEP_TIME), level=3, indent=2)
            sleep(CONST_REFRESH_SLEEP_TIME)

            try:
                more_buttom = self.client.find_element_by_class_name("ext-assignment-detail-more-handout-link")
                found = True
            except:
                found = False
        
        if not found:
            error = "Could not find 'more' button in the (%s) course -> (%s) lab blade. Returning." % (course_name, lab_name)
            log(error, level=0, indent=2)
            return None, error
            
        more_buttom.click()

        ############################################################################
        # Gets details of all the handouts of a selected lab in a course
        ############################################################################

        log("Getting (%s) course -> (%s) lab  handouts' details." % (course_name, lab_name), level=1)

        handouts_df, error = self.get_handouts_details(course_name, lab_name)

        return handouts_df, error


    def get_handouts_details(self, course_name, lab_name):
        """
        Gets the details of all the handouts of a selected lab in a course and returns them as a
            pandas dataframe.

        Arguments:
            course_name: the name of the course
            lab_name: the name of the lab

        Returns:
            handouts_df: pandas dataframe
        """

        data = []

        handouts_df = None
        error = None

        sleep_counter = 0
        found = False
        handout_list_table = None

        while not found and sleep_counter < CONST_MAX_REFRESH_COUNT:

            log("Sleeping while the (%s) course -> (%s) lab -> more blade: handout list table is loading (%.2f).." \
                % (course_name, lab_name, CONST_REFRESH_SLEEP_TIME), level=3, indent=4)

            sleep(CONST_REFRESH_SLEEP_TIME)

            try:
                handout_list_table = self.client.find_element_by_class_name("ext-classroster-grid")
                found = True
            except:
                found = False

            sleep_counter += 1
        
        if not found:
            error = "Could not load the (%s) course -> (%s) lab -> more blade: handout list table." \
                % (course_name, lab_name)
            log(error, level=0, indent=4)

            return handouts_df, error

        # Checks if the correct lab is loaded
        blade_titles = self.client.find_elements_by_class_name("fxs-blade-title-content")
        blade_titles_cnt = len(blade_titles)

        if blade_titles_cnt != 4:
            error = "Expected to be in the (%s) course -> (%s) lab -> more blade (depth = 4). Current depth = %d." % \
                (course_name, lab_name, blade_titles_cnt)

            log(error, level=0, indent=4)

            return handouts_df, error

        sleep_counter = 0
        consumption_loaded = False

        while not consumption_loaded and sleep_counter < CONST_MAX_REFRESH_COUNT:
            consumption_loaded = True
            
            log("Sleeping while the (%s) course -> (%s) lab -> more blade: handout list table is loading consumption data (%.2f).." \
                % (course_name, lab_name, CONST_REFRESH_SLEEP_TIME), level=3, indent=4)

            sleep(CONST_REFRESH_SLEEP_TIME)

            # Finding the list of handouts
            handout_list = handout_list_table.find_elements_by_class_name("azc-grid-row")

            # Getting details for handouts/subscriptions
            for handout in handout_list:
                
                handout_details = handout.find_elements_by_class_name("azc-grid-cellContent")
                
                if len(handout_details) < 6:
                    # something wrong, incorrect number of cells
                    continue

                handout_link = handout_details[0].find_element_by_class_name("ext-grid-clickable-link")

                handout_name = handout_link.text
                handout_budget = handout_details[3].text.lower()
                handout_consumed = handout_details[4].text.lower()
                handout_status = handout_details[5].text.lower()

                if handout_consumed == "--":
                    consumption_loaded = False
                    break
                
                handout_link.click()

                sub_status, sub_name, sub_id, sub_status, sub_user_email_list, crawltime_utc = self.get_handout_details(handout_name)
                
                if sub_status:
                    data.append([course_name, lab_name, \
                        handout_name, handout_budget, handout_consumed, handout_status, \
                        sub_name, sub_id, sub_status, sub_user_email_list, crawltime_utc])
                else:
                    error = "(%s) course -> (%s) lab -> (%s) handout subscription details could not be read!" \
                        % (course_name, lab_name, handout_name)
                    
                    log(error, level=0, indent=4)
                    break

            if error is not None:
                break

            sleep_counter += 1

        handouts_df = pd.DataFrame(data, 
            columns = ['Course name', 'Lab name', 'Handout name', 'Handout budget', 'Handout consumed', 'Handout status', \
                'Subscription name', 'Subscription id', 'Subscription status', 'Subscription users', 'Crawl time utc'])

        log("Finished getting the (%s) course -> (%s) lab -> more blade: handout details" \
            % (course_name, lab_name), level=1)

        return handouts_df, error


    def get_handout_details(self, handout_name):
        """
        Gets the handout details (sub_name, sub_id, sub_status, sub_user_email_list) from the
            Handout details blade. Checks if the correct handout is being selected by comparing
            subscription name with the handout name.

        Arguments:
            handout_name: handout name

        Returns:
            sub_details_loaded: a flag indicating if subscription details were read successfully
            sub_name, sub_id, sub_status, sub_user_email_list
        """

        sub_sleep_counter = 0
        sub_details_loaded = False
        sub_name = None
        sub_id = None
        sub_status = None
        sub_user_email_list = []

        while not sub_details_loaded and sub_sleep_counter < CONST_MAX_REFRESH_COUNT:

            log("Sleeping while handout (%s) details are loading (%f).." % (handout_name, CONST_REFRESH_SLEEP_TIME), level=3, indent=4)
            sleep(CONST_REFRESH_SLEEP_TIME)

            try:
                crawl_time_utc_dt = datetime.utcnow()

                sub_name = self.client.find_element_by_class_name("ext-classroom-handout-edit-subscription-name").text
                sub_id = self.client.find_element_by_class_name("ext-classroom-handout-edit-subscription-id").text
                sub_status = self.client.find_element_by_class_name("ext-classroom-handout-edit-subscription-status-data").text
                user_email_list = self.client.find_elements_by_class_name("ext-classroom-handout-edit-user-email")

                if sub_name == handout_name and len(user_email_list) > 0:
                    sub_details_loaded = True
                else:
                    continue

                for user_email_li in user_email_list:
                    try:
                        user_email = user_email_li.text
                    except:
                        user_email = None
                    
                    if user_email is not None:
                        sub_user_email_list.append(user_email)

            except:
                sub_details_loaded = False

            sub_sleep_counter += 1

        if sub_details_loaded:
            log("(%s) handout details read." % (handout_name), level=1, indent=2)
        else:
            log("Could not read (%s) handout details" % (handout_name), level=1, indent=2)

        return sub_details_loaded, sub_name, sub_id, sub_status, sub_user_email_list, crawl_time_utc_dt


    def get_eduhub_details(self):
        """
        Aggregates all the handout (subscriptions) details from all the courses/labs 
            into a pandas dataframe.

        """

        eduhub_df = None

        courses_df = self.get_courses_df()

        for _, course in courses_df.iterrows():

            course_df, error = self.get_course_details_df(course['Name'])
        
            if error is not None:
                break
            
            if eduhub_df is None:
                eduhub_df = course_df
            else:
                eduhub_df = eduhub_df.append(course_df)

        if error is None:
            return eduhub_df, error
        else:
            return None, error


    def quit(self):
        """
        Nicely turns off the crawler.

        """

        if self.client is not None:

            self.client.quit()

            self.client = None

