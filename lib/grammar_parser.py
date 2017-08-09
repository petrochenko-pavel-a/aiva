from textx.metamodel import metamodel_from_str
from textx.model import children_of_type
import operators
import yaml;
grammar = """
Model: seq = Call ('=>' seq*=Call)* ;

Call:  name= ID   '('args= ArgList ')' ;
ArgList: a= Arg? ( ',' a*=Arg) *;
Name: v= ID ;
Arg:
  (v =  Call | v =  INT | v =  Name | v =  BOOL | v =  STRING ) (m ='^')?;
"""

textGrammar="""
Seq: (seq*= OrExp )+;
Group: '(' seq=Seq ')' ( op = '+' |op = '?' |op = '*' )  ;
OrExp: options=Element ('|' options*=Element )* ;   
Element:  val = Assign | val= STRING | val = Group;
Assign: 
  name = ID  ( op='='|op='+='|op='*=') (val=ID | val=BOOL | val=NUMBER | val=STRING );
"""

transformModel = metamodel_from_str(grammar)
grammarModel= metamodel_from_str(textGrammar)


symbols={
    "propValueFilter": operators.FilterPropertyValue,
    "or": operators.Or,
    "and": operators.And,
    "select": operators.FilterPropertyValue
}
class OrParser:
    def __init__(self,options):
        self.options=options;
class SeqParser:
    def __init__(self,options):
        self.options=options;
class AssignParser:
    def __init__(self,name,op,val):
        self.name=name;
        self.op=op;
        self.val=val;
class GroupParser:
    def __init__(self,seq,op):
        self.op=op;
        self.seq=seq;
class StrParse:
    def __init__(self,str):
        self.str=str;

class Token:
    def __init__(self,name,val):
        self.name=name;
        self.val=val;
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
            return StrParse(m);
        raise ValueError()
class QueryComposer:
    def parseArg(self,el,vars):
        kind=type(el).__name__;
        if (kind=="Call"):
            return self.parseElement(el,vars);
        if (kind=="Name"):
            return vars[el.v];
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
        return const(*args);
    def composeFunction(self,str,vars):
        model=transformModel.model_from_str(str);
        chElements=[];
        for el in model.seq:
            chElements.append(self.parseElement(el,vars));
        return operators.Flow(chElements);

class TransformRule:
    def __init__(self,yml):
        self.pattern=RuleComposer().parseRuleModel(yml['definition'])
        self.transform=transformModel.model_from_str(yml['translation'])
        self.example=yml['example']
class RuleSet:

    def __init__(self,s):
        self.rules={};
        with open(s) as f:
            dataMap = yaml.safe_load(f)
            pt= dataMap['rules'];
            for key in pt:
                try:
                    self.rules[key]=TransformRule(pt[key]);
                except Exception as inst:
                    print "Error parting rule:"+key
                    print inst
v=RuleSet("/Users/kor/git/aml/examples/aiva/lib/grammar.yaml")