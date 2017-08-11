from textx.metamodel import metamodel_from_str
from textx.model import children_of_type
import operators
import yaml;
grammar = """
Model: seq = Call ('=>' (seq*=Call  ))* ;
Call:  name= ID   '('args= ArgList ')' (op='?')? ;
ArgList: a= Arg? ( ',' a*=Arg) *;
Name: v= ID ;
Arg:
  (v =  Call | v =  INT | v =  Name | v =  BOOL | v =  STRING ) (m ='^')?;
"""

textGrammar="""
Seq: (seq*= OrExp )+;
Group: '(' seq=Seq ')' ( op = '+' |op = '?' |op = '*' )?  ;
OrExp: options=Element ('|' options*=Element )* ;   
Element:  val = Assign | val= STRING | val = Group;
Assign: 
  name = ID  ( op='='|op='+='|op='*=') (val=ID | val=BOOL | val=NUMBER | val=STRING );
"""

transformModel = metamodel_from_str(grammar)
grammarModel= metamodel_from_str(textGrammar)

def orFunc(v):
    if type(v) in [list,set]:
        return operators.Or(v);
    return v;
def andFunc(v):
    if type(v) in [list,set]:
        return operators.And(v);
    return v;
def filterByVals(v):
    if (v):
        return operators.FilterByVals(v);
    return None;
def join(v):
    return v;
symbols={
    "propertyHasValue": operators.FilterPropertyValue,
    "partOf": operators.ParentValueFilter,
    "join": join,
    "flow": operators.Flow,
    "or": orFunc,
    "not": operators.Not,
    "countCompare": operators.CountCompare,
    "property": operators.TakePropertyValue,
    "and": andFunc,
    "select": operators.SelectInstances,
    "count": operators.CountInstances,
    "in": filterByVals
}
class OrParser:
    def __init__(self,options):
        self.options=options;


    def tryParse(self, ts):
        for o in self.options:
            ts.record();
            l = o.tryParse(ts);
            if (not l):
                ts.rollback();
            else:
                return True;
        return False

class SeqParser:
    def __init__(self,options):
        self.options=options;

    def tryParse(self, ts):
        for o in self.options:
            l=o.tryParse(ts);
            if (not l):
                return False;
        return True
parentValTypes={ "parentVal":"val"}
class AssignParser:
    def __init__(self,name,op,val):
        self.name=name;
        self.op=op;
        self.val=val;

    def tryParse(self, ts):
        v = ts.consume();
        if (v.type == self.val or (v.type in parentValTypes and parentValTypes[v.type]==self.val)):
            ts.storeVar(self.name,v,self.op);
            return True;
        return False;
class GroupParser:
    def __init__(self,seq,op):
        self.op=op;
        self.seq=seq;

    def tryParse(self, ts):
        parsed=False
        while True:
            ts.record();
            r=self.seq.tryParse(ts);
            if (r):
              parsed=True
              if (self.op=='?'):
                return True;
              if (self.op != '*' and self.op != '+' and self.op != '?'):
                  return True
            else:
                ts.rollback()
                if (self.op!='*' and self.op!='+' and self.op!='?'):
                    return False

                break;
        if (self.op=='+'):
            if (not parsed):return  False
        return True
class StrParse:
    def __init__(self,str):
        self.str=str;
    def tryParse(self,ts):
       v=ts.consume();
       if (v.type=="str" and v.val==self.str):
           return True;
       return False;
class Token:
    def __init__(self,name,val):
        self.name=name;
        self.val=val;
        self.type=name

    def __repr__(self):
        return str(self.name)+":"+str(self.val)
class RuleComposer:
    def parseRuleModel(self,model):
        if (isinstance(model,str)):
            return self.parseRuleModel(grammarModel.model_from_str(model))
        seq=[]
        for element in model.seq:
            els=[]
            for v in element.options:
                els.append(self.parseOption(v));
            if (len(els)==1):
                seq.append(els[0]);
            else: seq.append(OrParser(els));
        return SeqParser(seq)
    def parseOption(self,element):
        m = element.val
        c = type(m).__name__;
        if (c == 'Assign'):
            return AssignParser(m.name,m.op,m.val)
        if (c == 'Group'):
            return GroupParser(self.parseRuleModel(m.seq),m.op)
        if (c=='Element'):
            return self.parseOption(m);
        if (c=='str'):
            v=m.split(" ")
            if (len(v)>1):
                return SeqParser([StrParse(x) for x in v]);
            return StrParse(m);
        raise ValueError()
class QueryComposer:
    def parseArg(self,el,vars):
        kind=type(el).__name__;
        if (kind=="Call"):
            return self.parseElement(el,vars);
        if (kind=="Name"):
            if (el.v in vars):

                return vars[el.v];
            return None;
        return el;
    def parseArgList(self,el,vars):
        res=[];
        if el==None:
            return res;
        for a in el.a:
            res.append(self.parseArg(a.v,vars))
        return res;

    def parseElement(self,el,vars):
        const=None;
        if (el.name  in symbols):
            const=symbols[el.name];

        args=self.parseArgList(el.args,vars);

        if (const==None):
            if el.name in vars:
                return vars[el.name]
            if (el.op=='?'):
                return None
            raise ValueError(el.name)
        return const(*args);
    def composeFunction(self,str,vars):
        model=transformModel.model_from_str(str);
        return self.composeFromModel(model, vars)

    def composeFromModel(self, model, vars):
        chElements = [];
        for el in model.seq:
            fv=self.parseElement(el, vars);
            if (fv!=None):
                chElements.append(fv);
        if (len(chElements)==1):
            return chElements[0]
        return operators.Flow(chElements);


class TransformRule:
    def __init__(self,key,yml):
        self.key=key;
        self.pattern=RuleComposer().parseRuleModel(yml['definition'])
        self.transform=transformModel.model_from_str(yml['translation'])
        self.example=yml['example']
        if ('produces' in yml):
            self.produces=yml['produces']
        else: self.produces=self.key


class TryParse:
    def __init__(self,ts,i):
        self.ts=ts;
        self.i=i;
        self.value={}
        self.len=0;
        self.states=[]
    def storeVar(self,name,val,op):
        if (op=='+='):
            if (name in self.value):
                vl=self.value[name];
                if (isinstance(vl,list)):
                    vl.append(val.val);
                    return;
                else:
                    self.value[name]=[vl,val.val];
                    return;
        self.value[name]=val.val;
        return;


    def record(self):
        self.states.append((self.value.copy(),self.len));
    def consume(self):
        self.len=self.len+1;
        if (self.i + self.len)>len(self.ts):
            return Token("eof",None);
        return self.ts[self.i+(self.len-1)];
    def rollback(self):
        self.value,self.len=self.states.pop();
debug=False
class RuleSet:
    def parse(self,ts,ruleSet=None):
        p = True
        if (debug):
            print str(ts)+":<initial>"
        while p :
            p=False
            for rule in self.seq:

                if (ruleSet!=None):
                    if (not rule.key in ruleSet):
                        continue


                while True:
                    parsed = False;
                    for i in range(0,len(ts)):
                        t=TryParse(ts,i);
                        res=rule.pattern.tryParse(t);
                        if (res):
                            newVal = Token(rule.produces,t.value);
                            rm=QueryComposer().composeFromModel(rule.transform,t.value);
                            newVal.val=rm;
                            ts=replace(ts,i,t.len,newVal);
                            if debug:
                                print str(ts)+":"+rule.key

                            parsed=True;
                            p=True
                            break
                    if (not parsed or len(ts)==1):
                        break
            if (len(ts)==1):
                break
        return ts;
    def __init__(self,s):
        self.rules={};
        self.seq=[]
        with open(s) as f:
            dataMap = yaml.safe_load(f)
            pt= dataMap['rules'];
            for v in pt:
                key=v.keys()[0]
                try:
                    vr=TransformRule(key,v[key]);
                    self.rules[key]=vr;
                    self.seq.append(vr)
                except Exception as inst:
                    print "Error parting rule:"+key
                    print inst
v=RuleSet("C:/work/aiva/lib/grammar2.yaml")

def replace(v,startPos,tl,token):
    return v[0:startPos]+[token]+v[startPos+tl:len(v)]

def tokens(v):
    return [Token(name,value) for name,value in v]

def parse(t,ruleSet=None):
    return v.parse(t,ruleSet);
