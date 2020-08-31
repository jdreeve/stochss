import unittest
import time
import os
import selenium_test_setup_and_teardown
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


class TestFilesystem(unittest.TestCase):

    def setUp(self):
        self.browser_and_container = selenium_test_setup_and_teardown.setup()
        self.browser=self.browser_and_container[0]
        self.stochss_container=self.browser_and_container[1]
        self.vars = {}
   
    def tearDown(self):
        selenium_test_setup_and_teardown.teardown(self.browser, self.stochss_container)

    def wait_for_window(self, timeout = 2):
        time.sleep(round(timeout / 1000))
        wh_now = self.browser.window_handles
        wh_then = self.vars["window_handles"]
        if len(wh_now) > len(wh_then):
            return set(wh_now).difference(set(wh_then)).pop()

    def test_filesystem(self):

        #test close button on create directory modal window
        self.browser.find_element(By.CSS_SELECTOR, ".btn:nth-child(5)").click()
        self.browser.find_element(By.CSS_SELECTOR, ".dropdown-item:nth-child(1)").click()
        self.browser.find_element(By.ID, "modelNameInput").send_keys("uncreated_test_dir")
        self.browser.find_element(By.CSS_SELECTOR, ".btn-secondary").click()
        #test close button on create file modal window
        self.browser.find_element(By.CSS_SELECTOR, ".btn:nth-child(5)").click()
        self.browser.find_element(By.CSS_SELECTOR, ".dropdown-item:nth-child(2)").click()
        self.browser.find_element(By.ID, "modelNameInput").send_keys("uncreated_test_model")
        self.browser.find_element(By.CSS_SELECTOR, ".btn-secondary").click()
        #create new directory test_dir
        self.browser.find_element(By.CSS_SELECTOR, ".btn:nth-child(5)").click()
        self.browser.find_element(By.CSS_SELECTOR, ".dropdown-item:nth-child(1)").click()
        self.browser.find_element(By.ID, "modelNameInput").send_keys("test_dir")
        self.browser.find_element(By.CSS_SELECTOR, ".ok-model-btn").click()
        #create new model test_model
        self.browser.find_element(By.CSS_SELECTOR, ".page").click()
        self.browser.find_element(By.CSS_SELECTOR, ".btn:nth-child(5)").click()
        self.browser.find_element(By.CSS_SELECTOR, ".dropdown-item:nth-child(2)").click()
        self.browser.find_element(By.ID, "modelNameInput").send_keys("test_model")
        self.browser.find_element(By.CSS_SELECTOR, ".ok-model-btn").click()
        #return from Model Editor page to File Browser page
        self.browser.back()
        self.browser.wait_for_navigation_complete()
        
        #confirm create file and create directory successful
        jstree_nodes=self.browser.find_elements_by_class_name('jstree-node')
        print(jstree_nodes[0].text)
       # assert (jstree_nodes[0].text==(" /" + "\n" + " test_dir" + "\n" + " test_model.mdl" + "\n" + " Examples"))
        stochss_dir_contents = (self.stochss_container.exec_run("python -c \"import os;print(os.listdir())\"", demux=False)[1])
        assert not b"uncreated_test_model.mdl" in stochss_dir_contents
        assert not b"uncreated_test_dir" in stochss_dir_contents
        assert b"test_model.mdl" in stochss_dir_contents
        assert b"test_dir" in stochss_dir_contents

        #test upload StochSS model
        self.browser.find_element(By.CSS_SELECTOR, "b").click()
        self.browser.find_element(By.CSS_SELECTOR, ".dropdown-item:nth-child(4)").click()
        title=self.browser.find_element_by_class_name("modal-title")
        assert title.text=='Upload a model'
        self.browser.find_element(By.CSS_SELECTOR, ".info .btn-secondary").click()
        
        #test upload SBML model
        self.browser.find_element(By.CSS_SELECTOR, "b").click()
        self.browser.find_element(By.CSS_SELECTOR, ".dropdown-item:nth-child(5)").click()
        title=self.browser.find_element_by_class_name("modal-title")
        assert title.text=='Upload a sbml'
        self.browser.find_element(By.CSS_SELECTOR, ".info .btn-secondary").click()

        #test upload file
        self.browser.find_element(By.CSS_SELECTOR, "b").click()
        self.browser.find_element(By.CSS_SELECTOR, ".dropdown-item:nth-child(6)").click()
        title=self.browser.find_element_by_class_name("modal-title")
        assert title.text=='Upload a file'
        self.browser.find_element(By.CSS_SELECTOR, ".info .btn-secondary").click()

        #test collapse/expand jstree
        self.browser.find_element(By.CSS_SELECTOR, "#j1_1 > .jstree-icon").click()
        jstree_nodes=self.browser.find_elements_by_class_name("jstree-node")
        assert 1 == len(jstree_nodes)
        self.browser.find_element(By.CSS_SELECTOR, ".jstree-ocl").click()
        jstree_nodes=self.browser.find_elements_by_class_name("jstree-node")
        assert 4 == len(jstree_nodes)

        #test Actions For <node> button
        #test Edit (model)
        self.browser.find_element(By.ID, "j1_3_anchor").click()
        self.browser.find_element(By.CSS_SELECTOR, ".btn:nth-child(7)").click()
        self.browser.find_element(By.LINK_TEXT, "Edit").click()
        title=self.browser.find_element_by_class_name("modal-title")
        assert title.text=='Default Species Mode (required)'
        self.browser.back()
        self.browser.wait_for_navigation_complete()
        #test New Workflow
        self.browser.find_element(By.ID, "j1_3_anchor").click()
        self.browser.find_element(By.CSS_SELECTOR, ".btn:nth-child(7)").click()
        self.browser.find_element(By.LINK_TEXT, "New Workflow").click()
        table=self.browser.find_element_by_class_name("table")
        assert table.text=='StochSS Workflows\nEnsemble Simulation\nParameter Sweep'
        self.browser.back()
        self.browser.wait_for_navigation_complete()

        #test Convert To Notebook
        self.browser.find_element(By.ID, "j1_3_anchor").click()
        self.browser.find_element(By.CSS_SELECTOR, ".btn:nth-child(7)").click()
        self.vars["window_handles"] = self.browser.window_handles
        convert_menu_element = self.browser.find_element(By.LINK_TEXT, "Convert")
        ActionChains(self.browser).move_to_element(convert_menu_element).perform()
        time.sleep(1)
        self.browser.find_element(By.LINK_TEXT, "To Notebook").click()
        notebook_window_handle = self.wait_for_window(5000)
        root_handle = self.browser.current_window_handle
        self.browser.switch_to.window(notebook_window_handle)
        assert self.browser.find_element_by_id("ipython_notebook")
        self.browser.close()
        self.browser.switch_to.window(root_handle)

        stochss_dir_contents = (self.stochss_container.exec_run("python -c \"import os;print(os.listdir())\"", demux=False)[1])
        assert b'test_model.ipynb' in stochss_dir_contents

        #test Convert to SBML Model
        self.browser.find_element(By.ID, "j1_4_anchor").click()
        self.browser.find_element(By.CSS_SELECTOR, ".btn:nth-child(7)").click()
        convert_menu_element = self.browser.find_element(By.LINK_TEXT, "Convert")
        ActionChains(self.browser).move_to_element(convert_menu_element).perform()
        self.browser.find_element(By.LINK_TEXT, "To SBML Model").click()
        stochss_dir_contents = (self.stochss_container.exec_run("python -c \"import os;print(os.listdir())\"", demux=False)[1])
        assert b'test_model.sbml' in stochss_dir_contents
        
        #test Rename
        self.browser.find_element(By.ID, "j1_5_anchor").click()
        self.browser.find_element(By.CSS_SELECTOR, ".btn:nth-child(7)").click()
        self.browser.find_element(By.LINK_TEXT, "Rename").click()
        warnings=self.browser.find_elements_by_class_name("alert-warning")
        assert warnings[0].text=='You should avoid changing the file extension unless you know what you are doing!'

        #test Duplicate
        self.browser.find_element(By.CSS_SELECTOR, ".btn:nth-child(7)").click()
        self.browser.find_element(By.LINK_TEXT, "Duplicate").click()
        jstree_nodes=self.browser.find_elements_by_class_name("jstree-node")
        assert "test_model-copy.sbml" in jstree_nodes[0].text
        stochss_dir_contents = (self.stochss_container.exec_run("python -c \"import os;print(os.listdir())\"", demux=False)[1])
        assert b'test_model-copy.sbml' in stochss_dir_contents
        
        #test Delete
        self.browser.find_element(By.ID, "j1_4_anchor").click()
        jstree_nodes=self.browser.find_elements_by_class_name("jstree-node")
        self.browser.find_element(By.CSS_SELECTOR, ".btn:nth-child(7)").click()
        self.browser.find_element(By.LINK_TEXT, "Delete").click()
        self.browser.find_element(By.CSS_SELECTOR, ".yes-modal-btn").click()
        jstree_nodes=self.browser.find_elements_by_class_name("jstree-node")
        assert " test_model.sbml" not in jstree_nodes[0].text
        stochss_dir_contents = (self.stochss_container.exec_run("python -c \"import os;print(os.listdir())\"", demux=False)[1])
        assert b'test_model.sbml' not in stochss_dir_contents
