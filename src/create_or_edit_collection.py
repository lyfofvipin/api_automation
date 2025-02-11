import json, yaml
from os import getenv


class PrepareCollection():


    def __init__(self, tests_yaml_file: str = None, existing_collection_file : str = None) -> None:
        self.collection_template  = existing_collection_file if existing_collection_file else "src/templates/sample_collection.json"
        self.api_test_template = "src/templates/api_testcase_sample_collection.json"
        self.testsuite_api_template = "src/templates/test_suite_template.json"
        self.tests_yaml_data = tests_yaml_file if tests_yaml_file else "src/tests.yaml"

    def get_json_data_from_file(self, file_path : str = None) -> json:
        if file_path:
            with open(file_path, "r", encoding="utf-8") as template:
                return json.load(template)
    
    def collect_templates(self) -> None:
        self.collection_template: dict = self.get_json_data_from_file( self.collection_template )
        self.testsuite_api_template: dict = self.get_json_data_from_file( self.testsuite_api_template )

    def get_testdata(self) -> json:
        if self.tests_yaml_data:
            with open(self.tests_yaml_data, "r") as test_case_file:
                self.tests_yaml_data: dict = yaml.safe_load(test_case_file)

    def get_js_tests(self, file_path: str = None) -> list:
        with open(file_path, "r") as js_tests:
            return js_tests.readlines()

    def give_me_a_testcase(self, name: str, method: str, endpoint: str, js_testcase_file_path: str, body_raw: dict = {}) -> dict:
        api_template = self.get_json_data_from_file(self.api_test_template)
        api_template["name"] = name
        api_template["request"]["method"] = method
        api_template["request"]["url"]["raw"] = endpoint
        api_template["event"][0]["script"]["exec"] = [ x.replace("\n", "") for x in self.get_js_tests(js_testcase_file_path) ]
        if endpoint.startswith("http"):
            api_template["request"]["url"]["host"] = [ f"https://{endpoint.split('/')[2]}" ]
            api_template["request"]["url"]["path"] = endpoint.split("/")[3:]
        else:
            api_template["request"]["url"]["host"] = endpoint.split("/")[0]
            api_template["request"]["url"]["path"] = endpoint.split("/")[1:]
        if method == "POST" and body_raw:
            api_template["request"]["body"]["raw"] = body_raw
        return api_template

    def prepare_testsuite(self) -> list:
        testsuites_collection = []
        for x in self.tests_yaml_data:
            if x != "CollectionName":
                gather_testcase = self.give_me_a_testcase( \
                    self.tests_yaml_data.get(x).get("name"),\
                    self.tests_yaml_data.get(x).get("method"),\
                    self.tests_yaml_data.get(x).get("endpoint"),\
                    self.tests_yaml_data.get(x).get("js_testcase_file_path"),\
                    self.tests_yaml_data.get(x).get("body_raw")\
                )
                testsuites_collection.append(gather_testcase)
        return testsuites_collection

    def combine_testsuites(self):
        if self.collection_template["info"]["name"] == "dummy_testsuite_name":
            self.collection_template["info"]["name"] = self.tests_yaml_data.get("CollectionName")
            self.collection_template["item"] = self.prepare_testsuite()
        else:
            self.collection_template["item"].append(self.prepare_testsuite())
        print(json.dumps(self.collection_template))
        return json.dumps(self.collection_template)

    def dump_json_in_a_file(self):
        collection = self.combine_testsuites()
        with open("NewCollection.json") as collection_file:
            collection_file.write(collection)

if __name__ == "__main__":
    print("""
    This script will use the sample templates and will create a collection that can be run 
    using newman or postman.

    It will use the tests.yaml file to create a collection, testsuite and testcases
    If you want to pass your own file set a env variable TEST_SUITE_FILE="tests.yaml"

    You can pass a collection file also to append new testcases to an existing file
    for that just set a env variable EXISTING_COLLECTION="collection.json"\n\n
    """)
    EXISTING_COLLECTION = getenv("EXISTING_COLLECTION", None)
    TEST_SUITE_FILE = getenv("TEST_SUITE_FILE", None)
    generate_tests = PrepareCollection(TEST_SUITE_FILE, EXISTING_COLLECTION)
    generate_tests.collect_templates()
    generate_tests.get_testdata()
    generate_tests.dump_json_in_a_file()
