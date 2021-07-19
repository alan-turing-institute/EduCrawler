"""
EduHub portal crawling module.
"""

import os
from datetime import datetime, timedelta
from time import sleep, time
import pandas as pd
from tabulate import tabulate

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from webdriver_manager.chrome import ChromeDriverManager

from educrawler.utilities import log

from educrawler.constants import (
    CONST_PORTAL_ADDRESS,
    CONST_REFRESH_SLEEP_TIME,
    CONST_MAX_REFRESH_COUNT,
    CONST_SLEEP_TIME,
    CONST_COURSE_SLEEP_TIME,
    CONST_TIMEOUT,
    CONST_PORTAL_COURSES_ADDRESS,
    CONST_VERBOSE_LEVEL,
    CONST_ACTION_LIST,
    CONST_USAGE_ACTION,
    CONST_USAGE_PATH,
    CONST_USAGE_CSV_FILE_NAME,
    CONST_OUTPUT_TABLE,
    CONST_OUTPUT_CSV,
    CONST_OUTPUT_JSON,
    CONST_OUTPUT_DF,
    CONST_DEFAULT_OUTPUT_FILE_NAME,
    CONST_WEBDRIVER_HEADLESS,
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

        success = True
        error = None

        usage_file_path = os.path.join(
            CONST_USAGE_PATH, CONST_USAGE_CSV_FILE_NAME
        )

        if os.path.isfile(usage_file_path):
            os.rename(
                usage_file_path,
                "%s_backup_%s"
                % (usage_file_path, datetime.now().strftime("%Y%m%d_%H%M%S")),
            )

        options = Options()

        if hide:
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--log-level=0")

        options.add_experimental_option(
            "prefs",
            {
                "download.default_directory": r"%s" % (CONST_USAGE_PATH),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True,
            },
        )

        self.client = webdriver.Chrome(
            ChromeDriverManager().install(), options=options
        )

        log(
            "Logging to %s as %s" % (CONST_PORTAL_ADDRESS, login_email),
            level=1,
        )

        self.client.get(CONST_PORTAL_ADDRESS)

        sleep(CONST_SLEEP_TIME)

        # entering email address
        self.client.find_element_by_xpath("//input[@type='email']").send_keys(
            login_email
        )
        self.client.find_element_by_xpath("//input[@type='submit']").click()

        sleep(CONST_SLEEP_TIME)

        # check if username error occured
        try:
            _ = self.client.find_element_by_id("usernameError")
            success = False
            error = "Username might be incorrect. Stopping."
            log(error, level=0)
        except Exception:
            success = True

        if success:
            # entering password
            self.client.find_element_by_xpath(
                "//input[@name='passwd']"
            ).send_keys(login_pass)

            self.client.find_element_by_xpath(
                "//input[@type='submit']"
            ).click()

            sleep(CONST_SLEEP_TIME)

            # check if password error occured
            try:
                _ = self.client.find_element_by_id("passwordError")
                success = False
                error = "Password might be incorrect. Stopping."
                log(error, level=0)
            except Exception:
                error = False

        # wait until the mfa has been approved
        if success and mfa:

            log("Waiting for MFA approval.", level=1)

            sleep_counter = 0
            sleep_wait = True

            while sleep_wait and sleep_counter < CONST_MAX_REFRESH_COUNT:
                log(
                    "Sleeping (%f).." % (CONST_REFRESH_SLEEP_TIME),
                    level=3,
                    indent=2,
                )
                sleep(CONST_REFRESH_SLEEP_TIME)

                # wait for MFA approval if needed
                try:
                    _ = self.client.find_element_by_id("idDiv_SAOTCAS_Title")
                except Exception:
                    try:
                        self.client.find_element_by_xpath(
                            "//input[@type='submit']"
                        )

                        log("MFA approved!", level=1)
                        sleep_wait = False
                    except Exception:
                        sleep_wait = True

                sleep_counter += 1

            if sleep_wait:
                success = False
                error = "MFA was not approved! Stopping."
                log(error, level=0)

        if not success:
            self.client.quit()
            self.client = None
        else:
            # stay signed in
            self.client.find_element_by_xpath(
                "//input[@type='submit']"
            ).click()

            sleep(CONST_SLEEP_TIME)

    def get_courses(self):
        """
        Loads courses page

        Returns:
            success - flag if the action was succesful
            error - error message
            entries - a list of courses
        """

        success = True
        error = None

        log("Getting the list of courses", level=1)

        log("Loading %s" % (CONST_PORTAL_COURSES_ADDRESS), level=2, indent=2)
        self.client.get(CONST_PORTAL_COURSES_ADDRESS)

        sleep_wait = True
        time_start = time()

        # Finds table entries
        while sleep_wait:

            time_elapsed = time() - time_start

            if time_elapsed > CONST_TIMEOUT:
                success = False
                error = "ERROR: Time out (%d)" % (CONST_TIMEOUT)
                log(error, level=0)
                break

            log(
                "Sleeping while courses are loading (%f).."
                % (CONST_REFRESH_SLEEP_TIME),
                level=3,
                indent=2,
            )
            sleep(CONST_REFRESH_SLEEP_TIME)

            entries = self.client.find_elements_by_xpath(
                '//*[@class="fxs-portal-hover fxs-portal-focus azc-grid-row"]'
            )

            if len(entries) != 0:
                sleep_wait = False
                log("List of courses loaded!", level=2, indent=2)
                log("Found %d courses." % (len(entries)), level=1, indent=2)

        return success, error, entries

    def get_courses_df(self):
        """
        Gets the list of courses as pandas dataframe.

        Returns:
            success - flag if the action was succesful
            error - error message
            courses_df - courses dataframe
        """

        success, error, entries = self.get_courses()

        if not success:
            return success, error, None

        data = []

        for entry in entries:
            elements = entry.find_elements_by_class_name(
                "azc-grid-cellContent"
            )

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
                data.append(
                    [
                        course_name,
                        course_budget,
                        course_usage,
                        course_students,
                        course_project_groups,
                    ]
                )

        courses_df = pd.DataFrame(
            data,
            columns=[
                "Name",
                "Assigned credit",
                "Consumed",
                "Students",
                "Project groups",
            ],
        )

        return success, error, courses_df

    def get_course_details_df(
        self, course_name, lab_name=None, handout_name=None
    ):
        """
        Gets the list of handouts in a course and their details.

        Arguments:
            course_name: name of a course
            lab_name: name of a lab (optional)
            handout_name: name of a handout (optional)
        Returns:
            success - flag if the action was succesful
            error - error message
            details_df: pandas dataframe containing all the course's
                handouts and their details
        """

        sleep(CONST_COURSE_SLEEP_TIME)

        details_df = None

        log("Looking for %s course details" % (course_name), level=1)

        ###########################################################
        # first navigate to the courses page and wait till it loads
        ###########################################################

        success, error, entries = self.get_courses()

        if not success:
            return success, error, details_df

        ###########################################################
        # select the course
        ###########################################################

        found = False
        for entry in entries:
            elements = entry.find_elements_by_class_name(
                "azc-grid-cellContent"
            )

            if elements[0].text == course_name:
                log("(%s) course found." % (course_name), level=1)
                found = True
                break

        if not found:
            success = False
            error = "Could not find (%s) course. Returning." % (course_name)
            log(error, level=0)

            return success, error, details_df

        ###########################################################
        # wait until the course overview page is loaded
        ###########################################################

        elements[0].click()

        log("Loading (%s) course " % (course_name), level=1)

        found = False
        course_title = None

        timeout = False
        time_start = time()

        while not found:

            time_elapsed = time() - time_start
            if time_elapsed > CONST_TIMEOUT:
                timeout = True
                break

            log(
                "Sleeping while the (%s) course overview is loading (%f).."
                % (course_name, CONST_REFRESH_SLEEP_TIME),
                level=3,
                indent=2,
            )
            sleep(CONST_REFRESH_SLEEP_TIME)

            course_title_list = self.client.find_elements_by_class_name(
                "ext-classroom-overview-class-name-title"
            )

            if len(course_title_list) != 0:
                log("(%s) course overview loaded." % (course_name), level=2)
                found = True
                course_title = course_title_list[0].text

        if timeout:
            success = False
            error = "ERROR: Time out (%d)" % (CONST_TIMEOUT)
            log(error, level=0)
            return success, error, details_df

        if not found:
            success = False
            error = "Could not load (%s) course. Returning." % (course_name)
            log(error, level=0, indent=2)
            return success, error, details_df

        if course_title != course_name:
            success = False
            error = "The loaded course's title (%s) " % (
                course_title
            ) + "doesn't match the given name (%s)." % (course_name)
            log(error, level=0, indent=2)

            return success, error, details_df

        ###########################################################
        # finding all the labs that belong to the course and
        #   getting their details
        ###########################################################

        sleep(CONST_SLEEP_TIME)

        classroom_grid = self.client.find_element_by_class_name(
            "ext-classroom-overview-assignment-grid"
        )

        entries = classroom_grid.find_elements_by_class_name(
            "ext-grid-clickable-link"
        )

        log(
            "(%s) course has %d lab(s)." % (course_name, len(entries)), level=1
        )

        for element in entries:

            el_lab_name = element.text.lower()

            # are we are looking for a particular lab?
            if lab_name is not None and lab_name != el_lab_name:
                continue

            log(
                "Loading (%s) course -> (%s) lab blade."
                % (course_name, el_lab_name),
                level=1,
            )

            element.click()

            # give some time to load
            sleep(CONST_SLEEP_TIME)

            success, error, handouts_df = self.get_lab_details(
                course_name, el_lab_name, handout_name
            )

            if not success:
                break

            if details_df is None:
                details_df = handouts_df
            else:
                details_df = details_df.append(handouts_df)

            # if we found the lab, do not need to continue
            if lab_name is not None and lab_name == el_lab_name:
                break

        return success, error, details_df

    def get_lab_details(self, course_name, lab_name, handout_name=None):
        """
        Gets the details (handouts' details) of a selected lab.

        Arguments:
            course_name: the name of the course
            lab_name: the name of the lab
            handout_name: name of a handout (optional)
        Returns:
            success - flag if the action was succesful
            error - error message
            handouts_df: pandas dataframe
        """

        success = True
        error = None

        log(
            "Loading (%s) course -> (%s) lab -> more blade."
            % (course_name, lab_name),
            level=1,
        )

        found = False
        more_buttom = None

        time_start = time()
        timeout = False

        while not found:
            time_elapsed = time() - time_start
            if time_elapsed > CONST_TIMEOUT:
                timeout = True
                break

            log(
                "Sleeping while the initial handout list is loading (%f).."
                % (CONST_REFRESH_SLEEP_TIME),
                level=3,
                indent=2,
            )

            sleep(CONST_REFRESH_SLEEP_TIME)

            try:
                more_buttom = self.client.find_element_by_class_name(
                    "ext-assignment-detail-more-handout-link"
                )
                found = True
            except Exception:
                found = False

        if timeout:
            success = False
            error = "ERROR: Time out (%d)" % (CONST_TIMEOUT)
            log(error, level=0)
            return success, error, None

        if not found:
            success = False
            error = "Could not find 'more' button in the (%s) " % (
                course_name
            ) + "course -> (%s) lab blade. Returning." % (lab_name)
            log(error, level=0, indent=2)
            return success, error, None

        more_buttom.click()

        ###########################################################
        # Gets details of all the handouts of a selected lab in a course
        ###########################################################

        log(
            "Getting (%s) course -> (%s) lab  handouts' details."
            % (course_name, lab_name),
            level=1,
        )

        success, error, handouts_df = self.get_handouts_details(
            course_name, lab_name, handout_name
        )

        return success, error, handouts_df

    def get_handouts_details(self, course_name, lab_name, handout_name=None):
        """
        Gets the details of all the handouts of a selected lab in a course
            and returns them as a pandas dataframe.

        Arguments:
            course_name: the name of the course
            lab_name: the name of the lab
            handout_name: name of a handout (optional)
        Returns:
            success - flag if the action was succesful
            error - error message
            handouts_df: pandas dataframe
        """

        success = True
        error = None
        handouts_df = None

        data = []

        found = False
        handout_list_table = None

        time_start = time()
        timeout = False

        # wait until handout list table is loading
        while not found:

            time_elapsed = time() - time_start
            if time_elapsed > CONST_TIMEOUT:
                timeout = True
                break

            log(
                "Sleeping while the (%s) course -> " % (course_name)
                + "(%s) lab -> more blade: handout list " % (lab_name)
                + "table is loading (%.2f).." % (CONST_REFRESH_SLEEP_TIME),
                level=3,
                indent=4,
            )

            sleep(CONST_REFRESH_SLEEP_TIME)

            try:
                handout_list_table = self.client.find_element_by_class_name(
                    "ext-classroster-grid"
                )
                found = True
            except Exception:
                found = False

        if timeout:
            success = False
            error = "ERROR: Time out (%d)" % (CONST_TIMEOUT)
            log(error, level=0)
            return success, error, handouts_df

        if not found:
            success = False
            error = "Could not load the (%s) course -> " % (
                course_name
            ) + "(%s) lab -> more blade: handout list table." % (lab_name)
            log(error, level=0, indent=4)

            return success, error, handouts_df

        # Checks if the correct lab is loaded
        blade_titles = self.client.find_elements_by_class_name(
            "fxs-blade-title-content"
        )
        blade_titles_cnt = len(blade_titles)

        if blade_titles_cnt != 4:
            success = False
            error = (
                "Expected to be in the (%s) course -> " % (course_name)
                + "(%s) lab -> more blade (depth = 4). " % (lab_name)
                + "Current depth = %d." % (blade_titles_cnt)
            )
            log(error, level=0, indent=4)

            return success, error, handouts_df

        consumption_loaded = False

        time_start = time()
        timeout = False

        while not consumption_loaded:

            time_elapsed = time() - time_start
            if time_elapsed > CONST_TIMEOUT:
                timeout = True
                break

            consumption_loaded = True

            log(
                "Sleeping while the (%s) course -> " % (course_name)
                + "(%s) lab -> more blade: handout list table is " % (lab_name)
                + "loading consumption data "
                + "(%.2f).." % (CONST_REFRESH_SLEEP_TIME),
                level=3,
                indent=4,
            )

            sleep(CONST_REFRESH_SLEEP_TIME)

            # Finding the list of handouts
            handout_list = handout_list_table.find_elements_by_class_name(
                "azc-grid-row"
            )

            # Getting details for handouts/subscriptions
            for el_handout in handout_list:

                el_handout_details = el_handout.find_elements_by_class_name(
                    "azc-grid-cellContent"
                )

                if len(el_handout_details) < 6:
                    # something wrong, incorrect number of cells
                    continue

                el_handout_link = el_handout_details[
                    0
                ].find_element_by_class_name("ext-grid-clickable-link")

                el_handout_name = el_handout_link.text
                el_handout_budget = el_handout_details[3].text.lower()
                el_handout_consumed = el_handout_details[4].text.lower()
                el_handout_status = el_handout_details[5].text.lower()

                if el_handout_consumed == "--":
                    consumption_loaded = False
                    break

                # are we are looking for a particular handout?
                if (handout_name is not None) and (
                    handout_name != el_handout_name
                ):

                    continue

                el_handout_link.click()

                (
                    success,
                    error,
                    sub_name,
                    sub_id,
                    sub_status,
                    sub_expiry_date,
                    sub_user_email_list,
                    crawltime_utc,
                ) = self.get_handout_details(el_handout_name)

                if success:
                    data.append(
                        [
                            course_name,
                            lab_name,
                            el_handout_name,
                            el_handout_budget,
                            el_handout_consumed,
                            el_handout_status,
                            sub_name,
                            sub_id,
                            sub_status,
                            sub_expiry_date,
                            sub_user_email_list,
                            crawltime_utc,
                        ]
                    )
                else:
                    error = (
                        "(%s) course -> " % (course_name)
                        + "(%s) lab -> " % (lab_name)
                        + "(%s) handout subscription " % (el_handout_name)
                        + "details could not be read!"
                    )

                    log(error, level=0, indent=4)
                    break

                # if we found the handout, do not need to continue
                if (
                    handout_name is not None
                    and handout_name == el_handout_name
                ):
                    break

            if not success:
                break

        if timeout:
            success = False
            error = "ERROR: Time out (%d)" % (CONST_TIMEOUT)
            log(error, level=0)
            return success, error, handouts_df

        if not success:
            return success, error, handouts_df

        handouts_df = pd.DataFrame(
            data,
            columns=[
                "Course name",
                "Lab name",
                "Handout name",
                "Handout budget",
                "Handout consumed",
                "Handout status",
                "Subscription name",
                "Subscription id",
                "Subscription status",
                "Subscription expiry date",
                "Subscription users",
                "Crawl time utc",
            ],
        )

        log(
            "Finished getting the (%s) course " % (course_name)
            + "-> (%s) lab -> more blade: handout details" % (lab_name),
            level=1,
        )

        return success, error, handouts_df

    def get_handout_details(self, handout_name):
        """
        Gets the handout details
            (sub_name, sub_id, sub_status, sub_user_email_list)
            from the Handout details blade. Checks if the correct
            handout is being selected by comparing
            subscription name with the handout name.

        Arguments:
            handout_name: handout name

        Returns:
            success - a flag indicating if subscription details
                were read successfully
            error - error message
            sub_name, sub_id, sub_status, sub_expiry_date, sub_user_email_list
        """

        success = True
        error = None

        sub_details_loaded = False
        sub_name = None
        sub_id = None
        sub_status = None
        sub_expiry_date = None
        sub_user_email_list = []

        time_start = time()
        timeout = False

        while not sub_details_loaded:

            time_elapsed = time() - time_start
            if time_elapsed > CONST_TIMEOUT:
                timeout = True
                break

            log(
                "Sleeping while handout (%s) details are loading (%f).."
                % (handout_name, CONST_REFRESH_SLEEP_TIME),
                level=3,
                indent=4,
            )
            sleep(CONST_REFRESH_SLEEP_TIME)

            try:
                crawl_time_utc_dt = datetime.utcnow()

                sub_name = self.client.find_element_by_class_name(
                    "ext-classroom-handout-edit-subscription-name"
                ).text
                sub_id = self.client.find_element_by_class_name(
                    "ext-classroom-handout-edit-subscription-id"
                ).text

                user_email_list = self.client.find_elements_by_class_name(
                    "ext-classroom-handout-edit-user-email"
                )

                sub_status_data = self.client.find_elements_by_class_name(
                    "ext-classroom-handout-edit-subscription-status-data"
                )

                if len(sub_status_data) == 2:
                    sub_status = sub_status_data[0].text
                    try:
                        sub_expiry_date = datetime.strptime(
                            sub_status_data[1].text, "%b %d, %Y"
                        ).strftime("%Y-%m-%d")
                    except Exception:
                        sub_expiry_date = ""

                if sub_name == handout_name and len(user_email_list) > 0:
                    sub_details_loaded = True
                else:
                    continue

                for user_email_li in user_email_list:
                    try:
                        user_email = user_email_li.text
                    except Exception:
                        user_email = None

                    if user_email is not None:
                        sub_user_email_list.append(user_email)

            except Exception:
                sub_details_loaded = False

        if timeout:
            success = False
            error = "ERROR: Time out (%d)" % (CONST_TIMEOUT)
            log(error, level=0)

        if sub_details_loaded:
            log(
                "(%s) handout details read." % (handout_name),
                level=1,
                indent=2,
            )

        else:
            success = False
            error = "Could not read (%s) handout details" % (handout_name)
            log(error, level=1, indent=2)

        return (
            success,
            error,
            sub_name,
            sub_id,
            sub_status,
            sub_expiry_date,
            sub_user_email_list,
            crawl_time_utc_dt,
        )

    def get_eduhub_details(self, course_name=None):
        """
        Aggregates details of handouts (subscriptions) from courses/labs
            into a pandas dataframe.

        Arguments:
            course_name - name of a course

        Returns:
            success - flag if the action was succesful
            error - error message
            eduhub_df - aggregated details
        """

        eduhub_df = None

        success, error, courses_df = self.get_courses_df()

        if not success:
            return success, error, eduhub_df

        for _, course in courses_df.iterrows():

            self.client.refresh()
            success, error, course_df = self.get_course_details_df(
                course["Name"]
            )

            if not success:
                break

            if eduhub_df is None:
                eduhub_df = course_df
            else:
                eduhub_df = eduhub_df.append(course_df)

        return success, error, eduhub_df

    def download_usage(self, start_dt=None, end_dt=None):
        """
        Downloads usage data

        """

        if end_dt is None:
            end_dt = datetime.now()

        if start_dt is None:
            start_dt = end_dt - timedelta(days=10)

        success = True
        error = None

        # Opening courses page
        success, error, _ = self.get_courses()

        if not success:
            return success, error

        # Clicking the Usage button
        sleep(CONST_REFRESH_SLEEP_TIME)

        elements = self.client.find_elements_by_class_name(
            "azc-toolbarButton-label"
        )

        found = False
        for _, element in enumerate(elements):
            if element.text == "Usage":
                found = True
                break

        if not found:
            success = False
            error = "Could not find 'Usage' button"
            log(error, level=0, indent=2)
            return success, error

        element.click()

        sleep(CONST_SLEEP_TIME)

        # Changing the start date
        start_el = self.client.find_element_by_class_name(
            "azc-dateTimePicker-startDateTime"
        )

        end_el = self.client.find_element_by_class_name(
            "azc-dateTimePicker-endDateTime"
        )

        if start_el is None or end_el is None:
            success = False
            error = "Could not find 'Start' and 'End' input fields"
            log(error, level=0, indent=2)
            return success, error

        start_el_dt = start_el.find_element_by_class_name(
            "azc-datePicker"
        ).find_element_by_class_name("azc-input")

        start_el_tm = start_el.find_element_by_class_name(
            "azc-timePicker"
        ).find_element_by_class_name("azc-input")

        start_el_dt.clear()
        start_el_dt.send_keys(start_dt.strftime("%Y-%m-%d"))

        sleep(CONST_SLEEP_TIME)

        start_el_tm.clear()
        start_el_tm.send_keys(start_dt.strftime("%I:%M:%S %p"))

        sleep(CONST_SLEEP_TIME)

        start_el_tm.clear()
        start_el_tm.send_keys(start_dt.strftime("%I:%M:%S %p"))

        end_el_dt = end_el.find_element_by_class_name(
            "azc-datePicker"
        ).find_element_by_class_name("azc-input")

        end_el_tm = end_el.find_element_by_class_name(
            "azc-timePicker"
        ).find_element_by_class_name("azc-input")

        end_el_dt.clear()
        end_el_dt.send_keys(end_dt.strftime("%Y-%m-%d"))

        sleep(CONST_SLEEP_TIME)

        end_el_tm.clear()
        end_el_tm.send_keys(end_dt.strftime("%I:%M:%S %p"))

        sleep(CONST_SLEEP_TIME)

        end_el_tm.clear()
        end_el_tm.send_keys(end_dt.strftime("%I:%M:%S %p"))

        sleep(CONST_SLEEP_TIME)

        element = self.client.find_element_by_class_name(
            "fxc-fileDownloadButton"
        )

        element.click()

        # wait for the file to be downloaded
        sleep(60)

        # check if file exists

        usage_file_path = os.path.join(
            CONST_USAGE_PATH, CONST_USAGE_CSV_FILE_NAME
        )

        if not os.path.isfile(usage_file_path):
            success = False
            error = "Could not download usage data for %s - %s" % (
                start_dt,
                end_dt,
            )
            log(error, level=0, indent=2)

        return success, error

    def quit(self):
        """
        Nicely turns off the crawler.

        """

        if self.client is not None:

            self.client.quit()

            self.client = None


def crawl(args):
    """
    The main crawling routine.

    Arguments:
        args: command line arguments
    Returns:
        success - flag if the action was succesful
        error - error message
        return_result - if output is df - resulting dataframe
    """

    success = True
    error = None
    return_result = None

    # check if any action is specified
    if not (
        hasattr(args, "courses_action")
        or hasattr(args, "handout_action")
        or hasattr(args, "usage_action")
    ):

        success = False
        error = "Unrecognised/unspecified action. Skipping."
        log(error, level=0)

    if success:
        log("Crawler started", level=1)

        os.environ["WDM_LOG_LEVEL"] = "%d" % CONST_VERBOSE_LEVEL

        try:
            login_email = os.environ["EC_EMAIL"]
            login_password = os.environ["EC_PASSWORD"]
        except Exception:
            login_email = None
            login_password = None

        if (
            login_email is None
            or login_password is None
            or len(login_email) == 0
            or len(login_password) == 0
        ):

            success = False
            error = (
                "Missing login credentials. Have you "
                + "set the environmental parameters? Exiting."
            )
            log(error, level=0)

    if success:
        result = None

        try:
            webdriver_headless = os.environ["EC_HIDE"].lower() == "true"
        except Exception:
            webdriver_headless = CONST_WEBDRIVER_HEADLESS

        try:
            if os.environ["EC_MFA"].lower() == "false":
                mfa_on = False
            else:
                mfa_on = True
        except Exception:
            mfa_on = True

        # instantiate the crawler
        crawler = Crawler(
            login_email, login_password, hide=webdriver_headless, mfa=mfa_on
        )

        # take the specified action
        if crawler.client is not None:
            success, error, result = _take_action(args, crawler)
        else:
            success = False
            error = "Client not established"
            result = None

        crawler.quit()

        if success and result is not None:
            if args.output != CONST_OUTPUT_DF:
                _output_result(args.output, result)
            else:
                return_result = result

    log("Crawler finished", level=1)

    return success, error, return_result


def _take_action(args, crawler):
    """
    The main routine to handle all command line actions.

    Arguments:
        args: command line arguments
        crawler: eduhub crawler object

    """
    results_df = None

    if hasattr(args, "courses_action"):
        if args.courses_action == CONST_ACTION_LIST:
            success, error, results_df = crawler.get_courses_df()
        else:
            log("Unrecognised subaction. Skipping.", level=0)

    elif hasattr(args, "handout_action"):

        if hasattr(args, "course_name"):
            course_name = args.course_name
        else:
            course_name = None

        if hasattr(args, "lab_name"):
            lab_name = args.lab_name
        else:
            lab_name = None

        if hasattr(args, "handout_name"):
            handout_name = args.handout_name
        else:
            handout_name = None

        if args.handout_action == CONST_ACTION_LIST:
            # all courses
            if course_name is None:
                success, error, results_df = crawler.get_eduhub_details()
            # specific course (optionally, specific lab, handout)
            else:
                success, error, results_df = crawler.get_course_details_df(
                    course_name, lab_name, handout_name
                )

        else:
            log("Unrecognised subaction. Skipping.", level=0)

    elif hasattr(args, CONST_USAGE_ACTION):
        success, error = crawler.download_usage()

    else:
        log("Unrecognised/unspecified action. Skipping.", level=0)

    return success, error, results_df


def _output_result(output, result):
    """
    Outputs result of the action (if any) in the chosen format.

    Argument:
        output: command line argument for output
        result: result object of the previously taken action
    Returns:
        success - flag if the action was succesful
        error - error message
    """

    success = True
    error = None

    if not isinstance(result, pd.DataFrame):
        success = False
        error = "Expecting result as pandas dataframe. Got %s" % (type(result))
        log(error, level=0)
        return success, error

    if output == CONST_OUTPUT_TABLE:
        print(
            tabulate(result, headers="keys", tablefmt="psql", showindex=False)
        )

    elif output == CONST_OUTPUT_CSV:
        result.to_csv("%s.csv" % CONST_DEFAULT_OUTPUT_FILE_NAME)

    elif output == CONST_OUTPUT_JSON:
        result.to_json(
            "%s.json" % CONST_DEFAULT_OUTPUT_FILE_NAME, orient="records"
        )

    else:
        success = False
        error = "Unrecognised type of output. Skipping."
        log(error, level=0)

    return success, error
