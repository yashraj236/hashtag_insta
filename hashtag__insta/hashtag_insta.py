from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
from clarifai_grpc.grpc.api import service_pb2,service_pb2_grpc,resources_pb2
from clarifai_grpc.grpc.api.status import status_code_pb2
import datetime
import time
import pickle as  pkl
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec, wait
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup as bs

class WebDriverSetup:

    def __init__(self):
        self.driver = webdriver.Chrome(ChromeDriverManager().install())
    
    def ReturnDriver(self):
        return self.driver

class Analyze:

    def __init__(self,driver,tags):
        self.driver = driver
        self.url = "https://www.instagram.com"
        self.driver.get(self.url)
        self.tags = tags
        

    def login(self):
        username = input("Enter username of your instagram : ")
        password = input("Enter Password : ")
        action = ActionChains(self.driver)
        wait = WebDriverWait(self.driver,100)
        wait.until(ec.presence_of_element_located((By.XPATH,'/html/body/div[1]/section/main/article/div[2]/div[1]/div/form/div/div[1]/div/label/input')))
        
        userInput = self.driver.find_element_by_xpath("/html/body/div[1]/section/main/article/div[2]/div[1]/div/form/div/div[1]/div/label/input")
        action.click(userInput)
        action.perform()
        userInput.send_keys(username)
        
        password = self.driver.find_element_by_xpath("/html/body/div[1]/section/main/article/div[2]/div[1]/div/form/div/div[2]/div/label/input")
        action.click(userInput)
        action.perform()

        password.send_keys(password)
        
        login = self.driver.find_element_by_xpath("/html/body/div[1]/section/main/article/div[2]/div[1]/div/form/div/div[3]/button")
        action.click(on_element=login)
        action.perform()
        
        time.sleep(5)
        return self.Search(self.tags)
        
    def Search(self,tags):
        action = ActionChains(self.driver)
        TagLink = []
        for tag,val in tags.items():
            wait = WebDriverWait(self.driver,100)
            wait.until(ec.presence_of_element_located((By.XPATH,'/html/body/div[1]/section/nav/div[2]/div/div/div[2]/input')))
            
            SearchBar = self.driver.find_element_by_xpath("/html/body/div[1]/section/nav/div[2]/div/div/div[2]/input")
            SearchBar.send_keys("#"+tag)
            wait = WebDriverWait(self.driver,10)
            wait.until(ec.presence_of_element_located((By.CSS_SELECTOR,'div._01UL2 div.fuqBx div a.-qQT3')))
            wait = WebDriverWait(self.driver,100)
           
            FoundTags = self.driver.find_elements_by_css_selector("div._01UL2 div.fuqBx div a.-qQT3")
            for i in range(min(10,len(FoundTags))):
                try:
                    TagLink.append(FoundTags[i].get_attribute('href'))
                except:
                    pass
            SearchBar.clear()            

        
        return self.FindTopTags(TagLink)

    def FindTopTags(self,TagList):
        TagInfo = {}
        DateTimeFormat = '%Y-%m-%dT%H:%M:%S.%fZ'
        for tag in TagList:
            self.driver.get(tag)
            soup = bs(self.driver.page_source,"lxml")
            try:
                TotalPosts = soup.find('span',{'class':'g47SY'}).get_text()
            except:
                TotalPosts = 0
                print("\nok\n")
            PostLinks = []
            TimeDiff = []
            PostCount = 0
            for a in soup.find_all('a',href=True):
                PostLinks.append(a['href'])
            
            PostLinks = [x for x in PostLinks if x.startswith('/p/')][:5]
            try:
                self.driver.get('https://www.instagram.com'+str(PostLinks[0]))
                soup = bs(self.driver.page_source,"lxml")
                for j in soup.findAll('time'):
                    if j.has_attr('datetime'):
                        InitialDate = j['datetime'][:10]
                        break
            except:
                InitialDate = datetime.date.today().strftime("%Y-%m-%d")

                        
                       
            for i in range(len(PostLinks)):

                self.driver.get('https://www.instagram.com'+str(PostLinks[i]))
                soup = bs(self.driver.page_source,"lxml")
                for j in soup.findAll('time'):
                    if j.has_attr('datetime') and j['datetime'][:10]==InitialDate:
                        PostCount+=1
                        TimeDiff.append(j['datetime'])

            try:
                date1 = TimeDiff[0]
                date2 = TimeDiff[-1]
                diff = datetime.datetime.strptime(date2,DateTimeFormat) - datetime.datetime.strptime(date1,DateTimeFormat)
                freq = abs(int(diff.total_seconds()))
                TagInfo[tag.split('/')[-2]] = [TotalPosts,PostCount/freq]
            except:
                pass
            # print(TagInfo)
        # print(TagInfo)
        return TagInfo
        # print("end f2")

        
class SettingUp:

    def __init__(self,api_key):
        self.channel = ClarifaiChannel.get_grpc_channel()
        self.stub = service_pb2_grpc.V2Stub(self.channel)
        key = "Key "+api_key
        self.metadata = (("authorization",key),)
    
    def ReturnData(self):
        return (self.channel,self.stub,self.metadata)
    
class Find_Tags_Of_Image():

    def __init__(self,stub,metadata):
        
        self.stub = stub
        self.metadata = metadata
    
    def PredictTags(self,url):

        with open(url,"rb") as f:
            file = f.read()

        post_response_tag = self.stub.PostModelOutputs(
            service_pb2.PostModelOutputsRequest(
                model_id="aaa03c23b3724a16a56b629203edc62c",
                inputs=[
                    resources_pb2.Input(
                        data=resources_pb2.Data(
                            image=resources_pb2.Image(
                                base64=file
                            )
                        )
                    )
                ]
            ),
            metadata=self.metadata
        )

        if post_response_tag.status.code != status_code_pb2.SUCCESS:
            raise Exception("Prediction Model Failed with Status : ",post_response_tag.status.description)
        
        output = post_response_tag.outputs[0]
        Tags = {}
        for concept in output.data.concepts:
            if concept.value>0.95:
                Tags[concept.name] = concept.value
        return Tags


if __name__ == '__main__':
    
    key = "f9b77f67cba8465089c3cf7e03251c88"   # api key --> add the clarifai api key 
    
    setup = SettingUp(key) 
    channel,stub,metadata = setup.ReturnData()
    Predict = Find_Tags_Of_Image(stub,metadata)
    try:
        Cache = pkl.load(open("Cache.pkl","rb"))
    except:
        Cache = None
    FileUrl = r"" #  Add the File URL in your local machine for which you want to find the hashtags
    
    if Cache is None or FileUrl not in Cache:
        Tags = Predict.PredictTags(FileUrl)
        print(Tags)
        DriverObj = WebDriverSetup()
        driver = DriverObj.ReturnDriver()
        TagAnalysis = Analyze(driver,Tags)
        Report = TagAnalysis.login()
        Report = list(sorted(Report.items(),key=lambda x:int(x[1][0].replace(',',''))/x[1][1],reverse=True))
        temp = {}
        temp[FileUrl] = Report
        pkl.dump(temp,open("Cache.pkl","wb"))
        
    else:
        Report = Cache[FileUrl]

    print("Our Suggesstion of Hashtags for your Pic: \n")
    for info in Report:
        print(info[0],' Hashatg --> Total Posts : ',info[1]," and Post Frequency : ",info[2])