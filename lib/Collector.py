from github import Github
import vocabulary;
import uritemplate;
import api_client;
import json;
import yaml
import os.path
import dateparser
import spacy;
import nltk;
#nltk.download("wordnet", "/Users/kor/nltk_data")
from nltk.corpus import wordnet as wn
nlp= spacy.load("en");

# def syns()
#     res=set();
#     for s in wn.synsets('created'):
#         for w in s.lemmas():
#             print w.name()
try:
    import cPickle as pickle
except:
    import pickle
import pytz

utc=pytz.UTC

rc=api_client.Requestor();

class DateRange:
    def __init__(self,name,start,end):
        self.name=name;
        self.start=utc.localize(start);
        self.end=utc.localize(end);

    def filter(self,items):
        if (items==None):
            items=[self];
            return items;
        else:
            res=[]
            for q in items:
                ps=q.entity.props();
                for p in ps:
                    if (ps[p].yaml['range']=="datetime" and p in q.data):

                        vl = q.data[p];

                        try:
                            if (isinstance(vl,unicode)):
                                vl=dateparser.parse(vl);
                                if (vl>=self.start and vl<=self.end):
                                    res.append(q);
                        except:
                            continue;
            return res;

def filter_by_val(flt, items):
    rs = [];
    for q in items:
        for m in q.data:
            vl = q.data[m];
            if (vl == flt):
                rs.append(q);
                break;
            if (isinstance(vl, list) and len(vl) > 0):
                for v in vl:
                    if (v == flt):
                        rs.append(q);
                        break;
    return rs;
class Instance:
    def __init__(self,ent,data):
        self.entity=ent
        self.data=data;
        if 'html_url' in data:
            self.url=data['html_url']
        else:
            self.url=None
    def filter(self,items):
        if (items==None):
            items=[self];
            return items;
        else:
          return filter_by_val(self.data,items)



    def __repr__(self):
        return self.__str__()
    def __str__(self):
        name="";
        if 'name' in self.data and self.data['name']:
            name=self.data['name']

            return name.encode('utf-8')
        elif 'title' in self.data and self.data['title']:
            name=self.data['title'];
        elif 'login' in self.data and self.data['login']:
            name=self.data['login'];
        return name.encode('utf-8');
    def __hash__(self):
        return self.data['url'].__hash__();
class FilterableSet:
    def __init__(self,data,ds):
        self.data=data;
        self.ds=ds;
    def __iter__(self):
        return self.data.__iter__();
    def __len__(self):
        return self.data.__len__();
    def __getitem__(self, item):
        v= self.ds.filterInstances(item,self);
        return FilterableSet(v.data.intersection(self.data),self.ds)
class Collection:
    def __init__(self,name,yml,voc,defs):
        self.name=name;
        self.voc=voc;
        self.yml=yml;
        self.defs=defs;
        if 'url' in yml:
            self.url=yml['url']
        else:
            self.url="/"+name;
    def bind(self):
        self.range=self.defs.definition.entities[self.yml['range']];
ignoreList=['in',"of","and"]
class Entity:

    def __len__(self):
        return len(set(self))
    def __repr__(self):
        return "has class:"+self.name
    def __init__(self,name,yml,voc,defs):
        self.collections=[];
        self.definition=defs;
        self.name=name;
        self.voc=voc;
        self.clazz=voc.classTerm(name);
        self.selfUrl=yml['self'];
        if 'collections' in yml:
            for c in yml['collections']:
                col=yml['collections'][c];
                self.collections.append(Collection(c,col,voc,self))
    def __iter__(self):
        rs=[];
        for q in self.definition.cache.values():
            if '$type' in q and q['$type'].name==self.name:
                rs.append(Instance(self,q))
        return rs.__iter__();
    def domain(self):
        return self.voc.classTerm(self.name);
    def props(self):
        return self.domain().allProperties();
    def __getitem__(self, item):
        return self.filterInstances(item)


    def filter(self,vals):
        if vals==None:
            return set(self)
        s=set();
        for m in vals:
            if m.entity==self:
                s.add(m);
        return s;

    def filterInstances(self, item,items=None):
        if (isinstance(item, str)):
            ds = self.definition[item];
            if ds:
                item = ds;
        if (isinstance(item, list)):
            rs = [];
            for v in item:
                rs = rs + self[v];
            return rs;
        else:
            rs = []
            if not items: items=self;
            for q in items:
                for m in q.data:
                    vl = q.data[m];
                    if (vl == item):
                        rs.append(q);
                        break;
                    if (isinstance(vl, list) and len(vl) > 0):
                        for v in vl:
                            if (v == item):
                                rs.append(q);
                                break;
            return FilterableSet(set(rs),self);

    def url(self,args):
        return self.definition.base+uritemplate.expand(self.selfUrl,args)
    def load(self,name):
        val=self.fill(self.url(name));
        return val;
    def bind(self):
        for c in self.collections:
            c.bind();
    def __eq__(self, other):
        if(isinstance(other,Entity)):
            return self.name==other.name;
        return False;

    def fill(self,url,instance=None,always=False):
            if (url in self.definition.cache):
                return self.definition.cache[url];

            if always or len(self.collections)>0:
                result=rc.get(url);
                for col in self.collections:
                    collection=rc.readCollection(url+col.url);
                    filled=[];
                    for i in collection:
                        instance=col.range.fill(i['url'],i);
                        instance['$parent']=result;
                        filled.append(instance)
                        col.range.patch(instance)

                    result[col.name]=filled;
                self.definition.cache[url]=result;
                result['$type']=self;
                return result;
            self.definition.cache[url]=instance;
            if instance:
                instance['$type']=self;
            self.patch(instance)

            return instance;

    def patch(self, instance):
        ps = self.props();
        for q in ps:
            rs = ps[q]
            if rs.range and (rs.range.name in self.definition.entities):
                if (q in instance and instance[q] and 'url' in instance[q]):
                    rs=self.definition.entities[rs.range.name].fill(instance[q]['url'],instance[q],True)
                    instance[q]=rs;
                    self.definition.cache[rs['url']]=rs;
class Or:
    def __init__(self,l):
        self.list=[];
        for v in l:
            if (isinstance(v,Instance)):
                self.list.append(v);
            else: self.list.append(Instance(v,v['$type']))
    def filter(self,items):
        if (items==None):
            return self.list
        rs=set();
        for v in self.list:
            lst=filter_by_val(v,items);
            for l in lst:
                print l;
                rs.add(l)
        return rs;
class MatchPropertyVal:
    def __init__(self,prop,val):
        self.prop=prop;
        self.val=val;
    def __repr__(self):
        return self.__str__()
    def __str__(self):
        return str(self.prop)+":"+str(self.val)
    def filter(self,items):
        rs=[]
        if (items == None):
            return []
        for q in items:
            if (self.prop.name in q.data):
                vl = q.data[self.prop.name];
                if (vl==None):
                    continue
                if (vl == self.val or (isinstance(self.val,Instance) and vl['url']==self.val.data['url'])):
                    rs.append(q);
                    continue;
                if (isinstance(vl, list) and len(vl) > 0):
                        for v in vl:
                            if (v == self.val):
                                rs.append(q);
                                break;
                if (isinstance(self.val,Or)):
                    vls=self.val.list;
                    for j in vls:
                        if isinstance(vl,list):
                            for m in vl:
                                if (m['url']==j.data['url']):
                                    rs.append(q);
                                continue;
                        else:
                            if (vl['url']==j.data['url']):
                                rs.append(q);
                                continue;

        return rs;
def mergeTokens(i,tokens,maxNum,sep):
    res=tokens[i].text;
    for j in range(1,maxNum+1):
        if (i + j>len(tokens)-1):
            continue
        res=res+sep+tokens[i+j].text;
    return res
dates=[DateRange("last month",dateparser.parse("08.01.2017"),dateparser.parse("08.08.2017")),DateRange("this year",dateparser.parse("01.01.2017"),dateparser.parse("08.08.2017"))]

class ParsedToken:
    def __init__(self,val,token,ds):
        self.val=val;
        self.token=token;
        self.dependents=[]
        self.ds=ds;
    def __repr__(self):
        return self.__str__()
    def __str__(self):
        if len(self.dependents)>0:
            return str(self.val)+str(self.dependents)
        return str(self.val)
    def filter(self,items):
        if isinstance(self.val,unicode):
            if (items==None):
                items=self.ds.cache.values();
                newItems=[];
                for i in items:
                    if ('$type' in i):
                        inst=Instance(i['$type'],i);
                        newItems.append(inst)
                items=newItems;
            return filter_by_val(self.val,items)
        q= self.val.filter(items)
        for i in self.dependents: q=i.filter(q);
        return q;
class Definifion:
    def buildErCache(self):
        self.erCache={};
        for v in self.cache.values():
            if 'name' in v:
                self.recodNamedStuff(v['name'], v)
            if 'title' in v:
                self.recodNamedStuff(v['title'], v)

            if 'login' in v:
                self.recodNamedStuff(v['login'], v)
        for v in self.entities:
            n=v.lower();
            self.erCache[n]=self.entities[v];

    def entity(self,t):
        if self.erCache==None:
            self.buildErCache();
        if (t in self.erCache):
            return self.erCache[t];
        pr=self.voc.prop(t);
        if pr: return pr
        for m in dates:
            if (m.name==t):
                return m;
        return None;
    def entityFromToken(self,t,allowFuzzy=False):
        r=self.entity(t.text);
        if not r: r=self.entity(t.lemma_)
        if (not r) and allowFuzzy:
            if t.text.lower()!=t.text:
                for e in self.erCache:
                    if e and t.text in e:
                      return self.erCache[e];
        return r;
    def query(self,query):
        tokens=nlp(unicode(query));
        res=[]
        skipNext=0;
        lastParsed=None;
        for i in range(0,len(tokens)):
            t=tokens[i]
            if skipNext>0:

                skipNext=skipNext-1;
                continue

            ent=self.entityFromToken(t);
            if not ent:
               maxShift=6;
               if (maxShift>len(tokens)):
                   maxShift=len(tokens)-i;
               if maxShift>0:
                    for shift in range(1,maxShift):
                        text=mergeTokens(i,tokens,shift," ");
                        ent=self.entity(text);
                        if (ent):
                            skipNext=shift
                            break;
                        text=mergeTokens(i,tokens,shift,"");
                        ent=self.entity(text);
                        if (ent):
                            skipNext=shift
                            break;
                        text=mergeTokens(i,tokens,shift,"_");
                        ent=self.entity(text);
                        if (ent):
                            skipNext=shift
                            break;

            if not ent:
                ent=self.entityFromToken(t,allowFuzzy=True)
            ts=None;

            if (ent):
                if (isinstance(ent,Entity)):
                    ts=ent
                elif (isinstance(ent,list)):
                    ts=Or(ent)
                elif (isinstance(ent,vocabulary.PropertyTerm)):
                    ts=ent
                elif (isinstance(ent,DateRange)):
                    ts=ent
                else: ts=Instance(ent["$type"],ent)

            else:
                if (t.text in ignoreList):
                    continue

                ts=t.text;
            res.append(ParsedToken(ts,t,self));

        processedRes = self.postProcess(res)

        return processedRes;

    def postProcess(self, res):
        processedRes = []
        skipNext=0;
        for i in range(0, len(res)):
            t = res[i];
            if (skipNext > 0):
                skipNext = skipNext - 1;
                continue;
            if (isinstance(t.val, vocabulary.PropertyTerm)):
                if (i < len(res) - 1):
                    skipNext = 1;
                    processedRes.append(ParsedToken(MatchPropertyVal(t.val, res[i + 1].val),t.token,self))
            else:
                processedRes.append(t);
            processedRes=self.postProcess2(processedRes);
        while True:
            rs=self.postProcessDeps(processedRes)
            if (len(rs)==len(processedRes)):
                return rs;
            processedRes=rs;

    def postProcess2(self, res):
        processedRes = []
        skipNext=0;
        for i in range(0, len(res)):
            t = res[i];
            if (skipNext > 0):
                skipNext = skipNext - 1;
                continue;
            if (isinstance(t.val, MatchPropertyVal)):
                if (i < len(res) - 2):
                    if (res[i + 1].val=='or') and isinstance(res[i + 2].val,Instance):
                        skipNext=2;
                        t.val.val=Or([t.val.val,res[i+2].val]);
                        #continue;

            processedRes.append(t);
        return processedRes;
        # while True:
        #     rs=self.postProcess2(processedRes)
        #     if (len(rs)==len(processedRes)):
        #         return rs;
        #     processedRes=rs;


    def postProcessDeps(self, res):
        processedRes = []
        skipNext=0;
        for i in range(0, len(res)):
            t = res[i];
            if (skipNext > 0):
                skipNext = skipNext - 1;
                continue;
            if (i < len(res) - 1):
                    #print t.token.text+" "+str(t.token.head)
                    if (t.token.head==res[i+1].token):
                        res[i+1].dependents.append(t);
                        skipNext = 1;
                        processedRes.append(res[i+1])
                        continue
                    #processedRes.append(ParsedToken(MatchPropertyVal(t.val, res[i + 1].val),t.token))
            processedRes.append(t);
        return processedRes


    def executeQuery(self,query):
        ts=self.query(query);
        result=None;

        for t in ts:

            result=t.filter(result);
        return result;

    def recodNamedStuff(self, name, v):

        if (name==None):
            return;
        if name in self.erCache:
            val = self.erCache[name];
            if (isinstance(val, list)):
                val.append(v)
                return;
            else:
                self.erCache[name] = [val, v];
                return;
        else:
            self.erCache[name] = v;

    def __getitem__(self, item):
        if (item in self.entities):
            return self.entities[item];
        if (self.erCache==None):
            self.buildErCache();
        if (item in self.erCache):
                return self.erCache[item];
        return None;
    def __init__(self,path,voc,load=True):
        self.voc=voc;
        self.entities={};
        self.path=path;
        self.cache={};
        self.erCache=None
        with open(path) as f:
            api=yaml.load(f);
            self.base=api['base'];
            ent=api['entities'];
            for e in ent:
                entity=Entity(e,ent[e],voc,self);
                self.entities[str(e)]=entity
        for e in self.entities:
             self.entities[e].bind();
        if (load):
            self.loadCache()

    def propertyValues(self,name):
        s=set()
        for x in self.cache:
            if not '$type' in self.cache[x]:
                print self.cache[x]
            if name in self.cache[x]:
                s.add(self.cache[x][name])
        return s;

    def normalize(self,r):
        for v in r:
            if (isinstance(r[v],dict)):
                if 'url' in r[v]:
                    url=r[v]['url'];

                    if url in self.cache:
                        r[v]=self.cache[url];
                    else:
                        self.cache[url]=r[v];
            if (isinstance(r[v],list)):
                newList=[]
                for i in r[v]:
                    ps=False;
                    if ('url' in i):
                        if (i['url'] in self.cache):
                            newList.append(self.cache[i['url']]);
                            ps=True
                    if not ps:
                        newList.append(i);
                r[v]=newList;

    def load(self,type,id):
        e=self.entities[type];
        res= e.load(id);
        keys=[];
        for v in self.cache:
            keys.append(v);
        for c in keys:
            self.normalize(self.cache[c]);
        return res;
    def loadCache(self):
        if (os.path.isfile(self.path+".cache")):
            with open(self.path+".cache", 'rb') as handle:
                self.cache=pickle.load(handle)
    def storeCache(self):
        with open(self.path+".cache", 'wb') as handle:
                pickle.dump(self.cache, handle, protocol=pickle.HIGHEST_PROTOCOL)



#
# i=defs.executeQuery("issues")
# assert len(i)==2601
# i=defs.executeQuery("Denis issues")
# assert len(i)==181
# assert(len(defs.executeQuery("open Denis issues"))==18)
# assert (len(defs.executeQuery("closed Denis issues"))==163)
# assert (len(defs.executeQuery("open issues in raml-js-parser-2"))==66)
# assert (len(defs.executeQuery("open issues assigned to Konstantin"))==5)
# assert (len(defs.executeQuery("open issues assigned to Konstantin"))==5)
#
# print len(defs.executeQuery("open issues created by Konstantin"))
#
# print len(defs.executeQuery("open issues created by Konstantin in this year"))
# print defs.query("open issues created by Konstantin or Gleb in this year")
# print len(defs.executeQuery("open issues created by Konstantin or Gleb in this year"))
# print len(defs.executeQuery("open issues created by Konstantin or Christian in this year"))
#


#print defs.query()
#assert len(i)==2601
#print len(i);#2601
# l= defs['bug']
# #print l;
#
# #print defs['raml-spec']
# print len(defs['Issue']["Gleb Borisov"]['open']);
# for v in defs.erCache:
#     print v
# #    print q
# #print vl
# print len(defs['Label'])


###
###bugs
###issues closed by Gleb in last month
###labels in raml-js-parser-2
###print (("raml-spec"))