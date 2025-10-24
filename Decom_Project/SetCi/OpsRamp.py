import requests
import urllib.parse
import re
import time
from datetime import datetime, timedelta
import pytz
from dateutil.relativedelta import relativedelta


class OpsRamp:
    def __init__(self, clientKey, clientSecret, tenantId = None, subdomain = None ):
        """
        Initializes the OpsRamp client.

        Args:
        -
        >>> Arguments
            clientKey (str, optional): The client key.
            clientSecret (str, optional): The client secret.
            tenantId (str, optional): The tenant ID.
        """
        self.subdomain = subdomain or 'epsilon'
        self.tenantId = tenantId or '6408f21d-4e4a-3422-68d7-2527a2b463a4'
        self.__clientKey__ = clientKey
        self.__clientSecret__ = clientSecret
        self.Authenticate()
        self.Resource = Resource(self)
        self.Tags = Tags(self)
        self.Templates = Templates(self)
        self.CredentialSet = CredentialSet(self)
        self.ManagementProfile=ManagementProfile(self)
        self.APIv3=APIv3(self)
        self.PatchConfig = PatchConfig(self)
        self.Metrics = Metrics(self)
        self.Jobs = Jobs(self)
        self.ResourceGroup = ResourceGroup(self)
        self.getAll = getAll(self)
        self.timeHelpers = timeHelpers()

    def Authenticate(self):
        
        clientKey = self.__clientKey__
        clientSecret = self.__clientSecret__
        auth_url = f"https://{self.subdomain}.api.opsramp.com/tenancy/auth/oauth/token"
        auth_headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        auth_secret = {
            "grant_type": "client_credentials",
            "client_id": clientKey,
            "client_secret": clientSecret
        }
        encoded_token = urllib.parse.urlencode(auth_secret)
        authenticate = requests.post(auth_url, data=encoded_token, headers=auth_headers)
        response = self.handleResponse(self.Authenticate, [], authenticate, "Access Token")
        if response.get("access_token"):
            self.setHeader(response.get("access_token"))
        return response
    
    def setHeader(self,token):

        self.header = {'Content-Type':"application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"}

    def handleResponse(self,caller,args,response,msg):

        try:
            responseData = response.json()
        except Exception as e:
            responseData = ''

        if "throttled" in str(responseData):
            print("Server Throttled with Requests, Trying again")
            time.sleep(5)
            responseData = caller(*args)

        if "invalid_token" in str(responseData):
            self.Authenticate()
            responseData = caller(*args)
        
        if response.status_code == 200:
            # print(' ' * 50, end="\r",flush=True)
            print( f"{str(msg)} fetched successfully")
            return responseData if responseData else  True

        print(responseData)
        return responseData if responseData else  False
    
    def cleanCompare(self,a,op,b):

        clean_a = re.sub(r'[^a-zA-Z0-9]', '', a).lower()
        if type(b) is list:
            b = [re.sub(r'[^a-zA-Z0-9]', '', item).lower() for item in b]
            return eval(f"'{clean_a}' {op} b")
        clean_b = re.sub(r'[^a-zA-Z0-9]', '', b).lower()
        return eval(f"'{clean_a}' {op} '{clean_b}'")

class Resource:
    def __init__(self,OpsSelf):
        self.__OpsSelf__ =  OpsSelf
        self.subdomain = OpsSelf.subdomain
        self.tenantId = OpsSelf.tenantId
        self.header = OpsSelf.header
        self.handleResponse = OpsSelf.handleResponse
        # self.__dict__.update(vars(OpsSelf))

    def getWithParams(self,params):
        args = [params]
        query_string = urllib.parse.urlencode(params).replace('=',":")
        getResourceUrl=f"https://{self.subdomain}.api.opsramp.com/api/v2/tenants/{self.tenantId}/resources/search?queryString={query_string}"
        resource = requests.get(getResourceUrl,headers=self.header)
        response =  self.handleResponse(self.getWithParams, args, resource, f"{list(params.values())[0]} Resource")
        return response
    
    def getWithId(self,clientId,resourceId):
        args = [clientId,resourceId]
        resource = requests.get(f'https://{self.subdomain}.api.opsramp.com/api/v2/tenants/{clientId}/resources/{resourceId}',headers=self.header)
        response = self.handleResponse(self.getWithId, args, resource,f"{resourceId} Resource")
        return response
    
    def manage(self,clientId,resourceId):
        args = [clientId,resourceId]
        resource = requests.post(f'https://{self.subdomain}.api.opsramp.com/api/v2/tenants/{clientId}/devices/{resourceId}/manage',headers=self.header)
        response = self.handleResponse(self.manage, args, resource,f"{resourceId} Managed")
        return response

    def unManage(self,clientId,resourceId):
        args = [clientId,resourceId]
        resource = requests.post(f'https://{self.subdomain}.api.opsramp.com/api/v2/tenants/{clientId}/devices/{resourceId}/unmanage',headers=self.header)
        response = self.handleResponse(self.unManage, args, resource,f"{resourceId} Unmanaged")
        return response
    
    def getAvailabilityRule(self,clientId,resourceId):
        args = [clientId,resourceId]
        availabilityRule = requests.get(f'https://epsilon.api.opsramp.com/api/v2/tenants/{clientId}/resources/{resourceId}/availability/rule', headers=self.header)
        response = self.handleResponse(self.getAvailabilityRule,args,availabilityRule,f"Availability Rule for {resourceId}")
        return response
    
    def getAvailabilityInfo(self,clientId,resourceId, durationInDays = 14):
        args = [clientId,resourceId]
        end_time = int(time.time())
        start_time = end_time - (durationInDays * 24 * 60 * 60) # 14 days from ref code startTime=1638372063&endTime=1639581663
        availabilityInfo = requests.get(f'https://epsilon.api.opsramp.com/api/v2/tenants/{clientId}/resources/{resourceId}/availability?startTime={start_time}&endTime={end_time}', headers=self.header)
        response = self.handleResponse(self.getAvailabilityInfo,args,availabilityInfo,f"Availability Info for {resourceId}")
        return response
    
    def getOOBInterface(self,clientId,resourceId):
        args = [clientId,resourceId]
        availabilityRule = requests.get(f'https://epsilon.api.opsramp.com/api/v2/tenants/{clientId}/resources/{resourceId}/inventory/oobInterfaceCards', headers=self.header)
        response = self.handleResponse(self.getOOBInterface,args,availabilityRule,f"OOB Interface for {resourceId}")
        return response
    
class Tags:
    def __init__(self,OpsSelf):
        self.__OpsSelf__ =  OpsSelf
        self.subdomain = OpsSelf.subdomain
        self.tenantId = OpsSelf.tenantId
        self.header = OpsSelf.header
        self.handleResponse = OpsSelf.handleResponse

    def FilterTags(self,tags,filter_name):
        processedTags ={}
        for name in filter_name:
            processedTags[f"{name}"]=None
            for tag in tags:
                if self.__OpsSelf__.cleanCompare(name,"in",tag["name"]):
                    processedTags[f"{name}"] =  tag["value"]
                    break
        return processedTags

    def getAllWithClient(self,clientId,pageNo=1):
        args = [clientId,pageNo]
        query = {
        "objectType": "tag",
        "fields": ["id","name"],
        "pageSize":1000,
        "pageNo":pageNo
        }
        tags = requests.post(f'https://{self.subdomain}.api.opsramp.com/opsql/api/v3/tenants/{clientId}/queries',headers=self.header,json=query)
        response = self.handleResponse(self.getAllWithClient, args, tags,f"All Tags on Page {pageNo} for {clientId}")
        FullResponse = []
        PagedResponse = response
        nextFlag = PagedResponse.get("nextPage",False)
        FullResponse += PagedResponse.get("results")
        if nextFlag:
            FullResponse += self.getAllWithClient(clientId,pageNo+1)
        return FullResponse

    def getValues(self,clientId:str,tagId:str, pageNo=1):
        args = [clientId,tagId]
        values = requests.get(f'https://{self.subdomain}.api.opsramp.com/api/v3/tenants/{clientId}/tags/{tagId}/values?pageNo={pageNo}',headers=self.header)
        response = self.handleResponse(self.getValues, args, values,f"{tagId} Values")
        FullResponse = []
        PagedResponse = response
        nextFlag = PagedResponse.get("nextPage",False)
        FullResponse += PagedResponse.get("results")
        if nextFlag:
            FullResponse += self.getValues(clientId,tagId,pageNo+1)
        return FullResponse

    def create(self,clientId:str,newTags:list):
        args = [clientId,newTags]
        tag = requests.post(f'https://{self.subdomain}.api.opsramp.com/api/v3/tenants/{clientId}/tags',headers=self.header,json=newTags)
        response = self.handleResponse(self.create, args, tag,f"{clientId} new Tag created")
        return response

    def createValues(self,clientId:str,tagId:str,newValues:list):
        args = [clientId,tagId,newValues]
        values = requests.post(f'https://{self.subdomain}.api.opsramp.com/api/v3/tenants/{clientId}/tags/{tagId}/values',headers=self.header,json=newValues)
        response = self.handleResponse(self.createValues, args, values,f"{clientId} new Values created")
        return response

    def assign(self,clientId:str,tagId:str,valueId:str,entities:list):
        args = [clientId,tagId,valueId,entities]
        assigned = requests.post(f'https://{self.subdomain}.api.opsramp.com/api/v3/tenants/{clientId}/tags/{tagId}/values/{valueId}/tagged-entities',headers=self.header,json=entities)
        response = self.handleResponse(self.assign, args, assigned,f"{tagId} Tag with {valueId} Value is Added to {entities}")
        return response

    def unAssign(self,clientId:str,tagId:str,entities:list):
        args = [clientId, tagId, entities]
        assigned = requests.post(f'https://{self.subdomain}.api.opsramp.com/api/v3/tenants/{clientId}/tags/{tagId}/untagged-entities',headers=self.header,json=entities)
        response = self.handleResponse(self.unAssign, args, assigned,f"{tagId} Tag is Removed from {entities}")
        return response
    
    def forceGetTagId(self,tagName,clientId):
        AllTags = self.getAllWithClient(clientId)
        tagId=''
        for tag in AllTags:
            if self.__OpsSelf__.cleanCompare(tag["name"],"==",tagName):
                tagId = tag["id"]
                break
        if not tagId:
            tagId = self.create(clientId,[{"name":tagName}])[0]["id"]
            pass
        return tagId
    
    def forceGetValueId(self,tagId,valueName,clientId):
        AllTagValues = self.getValues(clientId,tagId)
        valueId = ''
        for TagValue in AllTagValues:
            if self.__OpsSelf__.cleanCompare(TagValue["value"],"==",valueName):
                valueId = TagValue["uniqueId"]
        if not valueId:
                valueId= self.createValues(clientId,tagId,[{"value":valueName}])[0]["id"]
        return valueId
    
    def forceGetTag_ValueId(self,tagName,valueName,clientId):
        tagId = self.forceGetTagId(tagName,clientId)
        valueId = self.forceGetValueId(tagId,valueName,clientId)
        return [tagId,valueId]
    
    def forceAssignTagValue(self,resourceIds:list,tagName,valueName,clientId):
        print(f"<<<<<< Assigning {tagName} : {valueName} >>>>>>>")
        entities = [{"entityType":"resource","entityId":resource} for resource in resourceIds]
        [tagId,valueId] = self.forceGetTag_ValueId(tagName,valueName,clientId)
        # Force Unassign previous values
        assignResult = self.assign(clientId,tagId,valueId,entities)
        if isinstance(assignResult, dict):
            if assignResult.get("code"):
                self.unAssign(clientId,tagId,entities)
                assignResult = self.assign(clientId,tagId,valueId,entities)
        return assignResult

    
class Templates:
    def __init__(self,OpsSelf):
        self.__OpsSelf__ =  OpsSelf
        self.subdomain = OpsSelf.subdomain
        self.tenantId = OpsSelf.tenantId
        self.header = OpsSelf.header
        self.handleResponse = OpsSelf.handleResponse

    def get(self,resourceId,clientId):
        args = [resourceId,clientId]
        templates=requests.get(f'https://{self.subdomain}.api.opsramp.com/api/v2/tenants/{clientId}/resources/{resourceId}/templates/search',headers=self.header)
        response = self.handleResponse(self.get, args, templates,f"{resourceId} Templates")
        return response
    

class Metrics:
    def __init__(self,OpsSelf):
        self.__OpsSelf__ =  OpsSelf
        self.subdomain = OpsSelf.subdomain
        self.tenantId = OpsSelf.tenantId
        self.header = OpsSelf.header
        self.handleResponse = OpsSelf.handleResponse
    
    def getWithQuery(self,filterDict,clientId,durationInMins:int=5,stepInMin:int=1,metricName=''):
        args = [filterDict,clientId,durationInMins,stepInMin,metricName]
        end_time = int(time.time())
        start_time = end_time - (durationInMins*60)
        formattedFilter = [f'{key}="{value}"' for key,value in filterDict.items()]
        filterString = "{" + ",".join(formattedFilter) + "}"        
        metrics=requests.get(f'https://{self.subdomain}.api.opsramp.com/metricsql/api/v3/tenants/{clientId}/metrics?query='+ metricName.replace(".","_") + filterString + f'&start={start_time}&end={end_time}&step={stepInMin*60}',headers=self.header)
        # metrics=requests.get(f'https://{self.subdomain}.api.opsramp.com/api/v2/metric/search?tenant={clientId}&rtype=DEVICE&&metric=cpu.fan.thermal.health&resource={resId}&startTime=1713246541&endTime=1713246841',headers=self.header)
        response = self.handleResponse(self.getWithQuery, args, metrics,f"All Metrics for {metricName} {clientId} with {filterDict}")
        return response


class CredentialSet:
    def __init__(self,OpsSelf):
        self.__OpsSelf__ =  OpsSelf
        self.subdomain = OpsSelf.subdomain
        self.tenantId = OpsSelf.tenantId
        self.header = OpsSelf.header
        self.handleResponse = OpsSelf.handleResponse

    def getAll(self,clientId):
        args = [clientId]
        credSets=requests.get(f'https://{self.subdomain}.api.opsramp.com/api/v2/tenants/{clientId}/credentialSets',headers=self.header)
        response = self.handleResponse(self.getAll, args, credSets,f"{clientId} Credential sets")
        return response
    
    def getForResource(self,resourceId,clientId):
        args =[resourceId,clientId]
        credSets=requests.get(f'https://{self.subdomain}.api.opsramp.com/api/v2/tenants/{clientId}/devices/{resourceId}/credentialSets/minimal',headers=self.header)
        response = self.handleResponse(self.getForResource, args, credSets,f"{resourceId} Credential sets")
        return response

    def set(self,clientId,credentialSetId,resourceId):
        args = [clientId,credentialSetId,resourceId]
        postData={"assignedDevices": [{"uniqueId": resourceId}]}
        credSets = requests.post(f'https://{self.subdomain}.api.opsramp.com/api/v2/tenants/{clientId}/credentialSets/{credentialSetId}',headers=self.header,json=postData)
        response = self.handleResponse(self.set, args, credSets,f"{resourceId} Credential sets")
        return response

class ManagementProfile:
    def __init__(self,OpsSelf):
        self.__OpsSelf__ =  OpsSelf
        self.subdomain = OpsSelf.subdomain
        self.tenantId = OpsSelf.tenantId
        self.header = OpsSelf.header
        self.handleResponse = OpsSelf.handleResponse

    def setToResource(self,clientId:str,resourceId:str,managementProfileName:str):
        args = [clientId, resourceId, managementProfileName]
        postData = {"managementProfile":managementProfileName}
        resource = requests.post(f'https://{self.subdomain}.api.opsramp.com/api/v2/tenants/{clientId}/resources/{resourceId}',headers=self.header,json=postData)
        response = self.handleResponse(self.setToResource, args, resource,f"{resourceId} mapping with {managementProfileName}")
        return response

    def get(self,clientId:str):
        args = [clientId]
        profiles = requests.get(f'https://{self.subdomain}.api.opsramp.com/api/v2/tenants/{clientId}/managementProfiles/search',headers=self.header)
        response = self.handleResponse(self.get, args, profiles,f"{clientId} All Management Profiles")
        return response

class APIv3:
    def __init__(self,OpsSelf):
        self.__OpsSelf__ =  OpsSelf
        self.subdomain = OpsSelf.subdomain
        self.tenantId = OpsSelf.tenantId
        self.header = OpsSelf.header
        self.handleResponse = OpsSelf.handleResponse

    def queryResources(self,query:str,fields:list,type:str="resource"):
        args = [query, fields, type]
        postData = {"objectType": type,
                    "fields": fields,
                    "filterCriteria": query}
        resources = requests.post(f'https://{self.subdomain}.api.opsramp.com/opsql/api/v3/tenants/{self.tenantId}/queries',headers=self.header,json=postData)
        response = self.handleResponse(self.queryResources, args, resources,f"{query}")
        return response

    def getClient(self,clientUUID):
        args = [clientUUID]
        client = requests.get(f'https://{self.subdomain}.api.opsramp.com/api/v2/tenants/{self.tenantId}/clients/{clientUUID}',headers=self.header)
        response = self.handleResponse(self.queryResources, args, client,f"{clientUUID}")
        return response
        


class PatchConfig:
    def __init__(self,OpsSelf):
        self.__OpsSelf__ =  OpsSelf
        self.subdomain = OpsSelf.subdomain
        self.tenantId = OpsSelf.tenantId
        self.header = OpsSelf.header
        self.handleResponse = OpsSelf.handleResponse

    def getAll(self,clientId,pageNo=1):
        args = [clientId, pageNo]
        profiles = requests.get(f'https://{self.subdomain}.api.opsramp.com/api/v2/tenants/{clientId}/patches/configurations/search?pageNo={pageNo}',headers=self.header)
        response = self.handleResponse(self.getAll, args, profiles,f"{clientId} All Patch Configuration groups on {pageNo}")
        FullResponse = []
        PagedResponse = response
        nextFlag = PagedResponse.get("nextPage",False)
        FullResponse += PagedResponse.get("results")
        if nextFlag:
            print( f'Fetching Page {pageNo+1} of {PagedResponse.get("totalPages")}',end="\r",flush=True)
            FullResponse += self.getAll(clientId,pageNo+1)
        return FullResponse
    
    def getDetails(self,clientId,configId):
        args = [clientId, configId]
        profiles = requests.get(f'https://{self.subdomain}.api.opsramp.com/api/v2/tenants/{clientId}/patches/configurations/{configId}',headers=self.header)
        response = self.handleResponse(self.getDetails, args, profiles,f"{configId} Detailed Patch Config")
        return response

    def newGroup(self,clientId,configName,maintenancePeriod,entityIds):
        args = [clientId,configName,maintenancePeriod,entityIds]
        groupInfo = {
        "patchConfigName": configName,
        "description": f"{configName}\nDon't Remove : 'Created By Script'",
        "approvalType": {"approvalType": 0},
        "rebootOptions": {
            "rebootRequired": True,
            "mandatoryReboot": False},
        "scheduleJob": {
            "entities": [{"resource": {
                "id": id,
                "type": "DEVICE"}} for id in entityIds],
            "script": {"jobType": "missingPatchesDownloadUpdate"},
            "schedule": {"startDate": "2024-04-14T10:10:10+0000",
                "pattern": {"type": "never"}}},
                "enablePatching": True,
        "maintenancePeriod": maintenancePeriod}
        
        Config = requests.post(f'https://{self.subdomain}.api.opsramp.com/api/v2/tenants/{clientId}/patches/configurations',headers=self.header,json=groupInfo)
        response = self.handleResponse(self.newGroup, args, Config,f"{configName} new Patching Group with {entityIds}")
        return response
    
    def addResource(self,clientId,patchConfigId,entities):
        args = [clientId,patchConfigId,entities]
        groupInfo = self.getDetails(clientId,patchConfigId)
        existingEntities = groupInfo.get("scheduleJob",{}).get("entities",[])
        filteredEntities = [{"resource": {"id": id,"type": "DEVICE"}} for id in entities if id not in [entity.get("resource",{}).get("id") for entity in existingEntities]]
        groupInfo["scheduleJob"]["schedule"]["startDate"] =  "2024-04-14T10:10:10+0000"
        if existingEntities:
            existingEntities += filteredEntities
        else:
            groupInfo["scheduleJob"]["entities"] = filteredEntities
        config = requests.post(f'https://{self.subdomain}.api.opsramp.com/api/v2/tenants/{clientId}/patches/configurations/{patchConfigId}',headers=self.header,json=groupInfo)
        response = self.handleResponse(self.addResource, args, config,f'{groupInfo.get("patchConfigName")} Patching Group updated')
        return response
    
    def getName(self,servers,clientUUID):
        Invalid_SNames=[server for server in servers if 8<len(server)<11]
        if Invalid_SNames:
            return f"{Invalid_SNames} Server Names are Invalid"
        uniq_prefix = list(set([server[:8].upper() for server in servers]))
        env_abbr = {"P":"PROD","D":"DEV","U":"UAT","F":"DR","Q":"QA","S":"STG"}
        envir = list(set([env[0] for env in uniq_prefix]))
        loc = list(set([env[1:3] for env in uniq_prefix]))
        os = list(set([env[3] for env in uniq_prefix]))
        # client = list(set([env[4:8] for env in uniq_prefix]))
        client = [self.__OpsSelf__.APIv3.getClient(clientUUID).get('name','').split('(')[0].strip()]
        if len(envir) > 1 or len(os) > 1 or len(client) > 1 :
            return f"Invalid : \n envir  > {envir}\n Os > {os}\n client {client}"
        else:
            return f"{client[0].upper()}-{env_abbr[envir[0].upper()]}-{os[0].upper()}-{'_'.join(loc).upper()}"
        
    def installStatus(self,clientId, resourceId):
        args = [clientId, resourceId]
        installStatus = requests.get(f'https://{self.subdomain}.api.opsramp.com/api/v2/tenants/{clientId}//resources/{resourceId}/patches/install/status',headers=self.header)
        response = self.handleResponse(self.installStatus, args, installStatus,f"Patch Install Status for {resourceId}")
        return response
    
    def scanStatus(self,clientId, resourceId):
        args = [clientId, resourceId]
        scanStatus = requests.get(f'https://{self.subdomain}.api.opsramp.com/api/v2/tenants/{clientId}//resources/{resourceId}/patches/scan/status',headers=self.header)
        response = self.handleResponse(self.scanStatus, args, scanStatus,f"Patch Scan Status for {resourceId}")
        return response

    def removeResource(self,clientId,patchConfigId,entities):
        args = [clientId,patchConfigId,entities]
        groupInfo = self.getDetails(clientId,patchConfigId)
        groupInfo.get("scheduleJob",{})["entities"] = [entity for entity in groupInfo.get("scheduleJob",{}).get("entities",[]) if entity.get("resource",{}).get("id") not in entities]
        config = requests.post(f'https://{self.subdomain}.api.opsramp.com/api/v2/tenants/{clientId}/patches/configurations/{patchConfigId}',headers=self.header,json=groupInfo)
        response = self.handleResponse(self.removeResource, args, config,f'{groupInfo.get("patchConfigName")} Patching Group removing resources')
        return response
    
class Jobs:
    def __init__(self,OpsSelf):
        self.__OpsSelf__ =  OpsSelf
        self.subdomain = OpsSelf.subdomain
        self.tenantId = OpsSelf.tenantId
        self.header = OpsSelf.header
        self.handleResponse = OpsSelf.handleResponse

    def getAll(self,clientId,pageNo=1):
        args = [clientId, pageNo]
        jobsResponse = requests.get(f'https://{self.subdomain}.api.opsramp.com/api/v2/tenants/{clientId}/jobs/search?pageNo={pageNo}',headers=self.header)
        response = self.handleResponse(self.getAll, args, jobsResponse,f"All Jobs on {clientId} at PageNo {pageNo}")
        FullResponse = []
        PagedResponse = response
        # print(response)
        nextFlag = PagedResponse.get("nextPage",False)
        FullResponse += PagedResponse.get("results")
        if nextFlag:
            print( f'Fetching Page {pageNo+1} of {PagedResponse.get("totalPages")}',end="\r",flush=True)
            FullResponse += self.getAll(clientId,pageNo+1)
        return FullResponse

    
    def getDetails(self,clientId,jobId):
        args = [clientId, jobId]
        jobResponse = requests.get(f'https://{self.subdomain}.api.opsramp.com/api/v2/tenants/{clientId}/jobs/{jobId}',headers=self.header)
        response = self.handleResponse(self.getDetails, args, jobResponse,f"Detailed Job info {jobId}")
        return response
        
    def new(self,clientId,jobName,entityIds):
        args = [clientId, jobName, entityIds]
        jobTemplate= {
            'name': jobName,
            "entities": [{"resource": {"id": id,"type": "DEVICE"}} for id in entityIds],
            'schedule': {'startDate': '2024-12-19T00:00:00+0000',
                        'pattern': {'type': 'daily', 'frequency': 'everyday'},
                        'daysToAdd': 0},
                        'jobQueued': False,
                        'script': {'jobType': 'missingPatchesRequest'},
                        'requiredParams': []}

        jobResponse = requests.post(f'https://{self.subdomain}.api.opsramp.com/api/v2/tenants/{clientId}/jobs',headers=self.header,json=jobTemplate)
        response = self.handleResponse(self.new, args, jobResponse,f"new Job '{jobName}' on {entityIds}")
        return response
    
    def addResource(self,clientId,jobId,entityIds):
        args = [clientId, jobId, entityIds]
        jobInfo = self.getDetails(clientId,jobId)
        alreadyExistingRes = [entity.get("resource",{}).get("id") for entity in jobInfo.get("entities",[]) if entity.get("resource",{}).get("id") in entityIds]
        newEntities = [{"resource": {"id": id,"type": "DEVICE"}} for id in entityIds if id not in alreadyExistingRes]
        if newEntities == []:
            print( f"All Entities {entityIds} are Already in the Same Job")
            return "All Entities are Already in the Same Job"
        
        if jobInfo.get("entities",[]):
            jobInfo["entities"]+=newEntities
        else:
            jobInfo["entities"]=newEntities
        
        jobResponse = requests.post(f'https://{self.subdomain}.api.opsramp.com/api/v2/tenants/{clientId}/jobs/{jobId}',headers=self.header,json=jobInfo)
        response = self.handleResponse(self.addResource, args, jobResponse,f'Adding resources {[entity.get("resource",{}).get("id") for entity in newEntities]} to {jobId}')
        return response
    
    def safeAddResource(self,clientId,jobId,entityIds):
        AllJobs=self.getAll(clientId)
        AllJobs = [job for job in AllJobs if job.get("script",{}).get("jobType") == "missingPatchesRequest"]
        AllJobDetails=[]
        for job in AllJobs:
            AllJobDetails.append(self.getDetails(clientId,job.get("id")))
        jobInfo = self.getDetails(clientId,jobId)
        alreadyExistingRes = [entity.get("resource",{}).get("id") for entity in jobInfo.get("entities",[]) if entity.get("resource",{}).get("id") in entityIds]
        AllExistingRes=[entity.get("resource",{}).get("id") for job in AllJobDetails for entity in job.get("entities",[]) ]
        conflictRes = [id for id in entityIds if (id not in alreadyExistingRes) and (id in AllExistingRes) ]
        newEntities = [id for id in entityIds if id not in AllExistingRes ]
        
        if conflictRes : print(f"{conflictRes} Already in Other Job")
        if alreadyExistingRes : print(f"{alreadyExistingRes} Already in Same Job")
        response = "Resources are Empty after Filtering"
        if newEntities: 
            response = self.addResource(clientId,jobId,newEntities)
        else: print(response)
        
        return response

class ResourceGroup:
    def __init__(self,OpsSelf):
        self.__OpsSelf__ =  OpsSelf
        self.subdomain = OpsSelf.subdomain
        self.tenantId = OpsSelf.tenantId
        self.header = OpsSelf.header
        self.handleResponse = OpsSelf.handleResponse

    def getAll(self,clientId):
        args = [clientId]
        ResourceGroups = requests.get(f'https://{self.subdomain}.api.opsramp.com/api/v2/tenants/{clientId}/deviceGroups/minimal',headers=self.header)
        response = self.handleResponse(self.getAll, args, ResourceGroups,f" All Resource Groups on {clientId}")
        return response
    
    def getDetails(self,clientId,resourceGroupId):
        args = [clientId, resourceGroupId]
        resourceGroup = requests.get(f'https://{self.subdomain}.api.opsramp.com/api/v2/tenants/{clientId}/deviceGroups/{resourceGroupId}',headers=self.header)
        response = self.handleResponse(self.getDetails, args, resourceGroup,f"Detailed Job info {resourceGroupId}")
        return response
    
    def newGroup(self,clientId,GroupName):
        args = [clientId, GroupName]
        GroupTemplate= [{
                        'name': GroupName.upper(),
                        'description':GroupName.capitalize(),
                        'linkedService': False,
                        'rootVisibility': True,
                        'type': 'DEVICE_GROUP',
                        'entityType': 'DEVICE_GROUP'}]

        
        groupResponse = requests.post(f'https://{self.subdomain}.api.opsramp.com/api/v2/tenants/{clientId}/deviceGroups',headers=self.header,json=GroupTemplate)
        response = self.handleResponse(self.newGroup, args, groupResponse,f"new Resource Group '{GroupName.upper()}'")
        return response

    def addResource(self,clientId,resourceGroupId,entityIds):
        args = [clientId,resourceGroupId,entityIds]
        newEntities = [{"id": id,"type": "DEVICE"} for id in entityIds]
        GroupResourceResponse = requests.post(f'https://{self.subdomain}.api.opsramp.com/api/v2/tenants/{clientId}/deviceGroups/{resourceGroupId}/childs',headers=self.header,json=newEntities)
        response = self.handleResponse(self.addResource, args,GroupResourceResponse,f"Adding resources {entityIds} to Resource Group {resourceGroupId}")
        return response

class getAll:
    def __init__(self,OpsSelf):
        self.__OpsSelf__ =  OpsSelf
        self.subdomain = OpsSelf.subdomain
        self.tenantId = OpsSelf.tenantId
        self.header = OpsSelf.header
        self.handleResponse = OpsSelf.handleResponse
    
    def clients(self,pageNo=1):
        args = [pageNo]
        allClients = requests.get(f'https://{self.subdomain}.api.opsramp.com/api/v2/tenants/{self.tenantId}/clients/search?pageNo={pageNo}',headers=self.header)
        response = self.handleResponse(self.clients, args, allClients, f" All Clients on Page {pageNo}")
        FullResponse = []
        PagedResponse = response
        nextFlag = PagedResponse.get("nextPage",False)
        FullResponse += PagedResponse.get("results")
        if nextFlag:
            FullResponse += self.clients(pageNo+1)
        return FullResponse

class timeHelpers:
    def convert_to_utc(time_value, time_zone):
        """Converts a given time (HH:MM:SS) from a timezone to UTC."""
        if isinstance(time_value, 'str'):
            time_value = datetime.strptime(time_value, "%H:%M:%S").time()
        today = datetime.today().date()
        local_tz = pytz.timezone(time_zone)
        local_time = local_tz.localize(datetime.combine(today, time_value))
        return local_time.astimezone(pytz.utc)

    def find_next_occurrence(time_value, time_zone, recurrence, week_no, weekday, start_date):
        """Finds the next occurrence based on recurrence type."""
        # today = datetime.today()
        
        if recurrence == "monthly":
            next_date = start_date + relativedelta(months=1, day=1)
        elif recurrence == "quarterly":
            next_date = start_date + relativedelta(months=3, day=1)
        elif recurrence == "yearly":
            next_date = start_date + relativedelta(years=1, day=1)
        
        while next_date.isoweekday() != weekday:
            next_date += timedelta(days=1)
        
        next_date += timedelta(weeks=week_no - 1)  # Adjust for nth occurrence
        
        local_tz = pytz.timezone(time_zone)
        local_datetime = local_tz.localize(datetime.combine(next_date, time_value))
        return local_datetime.astimezone(pytz.utc)