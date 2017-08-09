import spacy;
nlp= spacy.load("en");
from spacy.symbols import *

class Argument:

    def __init__(self,name,consumeEverything=False,required=False):
        self.name=name;
        self.consumeEverything=consumeEverything;
        self.value=[];
        self.required=required


    def toString(self):
        return self.name+"="+str(self.value)+";";

    def consume(self,tokens):
        vl="";
        consumed=set();
        value=set();
        if (self.consumeEverything):
            consumed=set(tokens)
            value=set(tokens);
            tokens-=consumed;
        for t in tokens:
            if (t.text==self.name):
                if (t.i>0):
                    l=t.doc[t.i-1]
                    if (self.canConsume(l)):
                        consumed.add(l);
                        value.add(l);
                consumed.add(t)
        tokens-=consumed;
        for i in value:
            text=""
            for l in i.lefts:
                text+=l.text+" "
            text+=i.text+" ";
            for r in i.rights:
                text+=(r.text)+" "
            self.value.append(text);
    def canConsume(self,v):
        return True;
class ArgWithValues(Argument):
   def __init__(self,name,vals,consumeEverything=False,required=False):
       super.__init__(self,name,consumeEverything,required)
       self.vals=vals;
   def canConsume(self,v):
       return v in self.vals;
class Action:
    def id(self):
        return self._verb.id()+" "+self._names[0]

    def addAnyArg(self,v):
        self.anyArg=v;
        v.consumeEverything=True;

    def addArg(self,a):
        self._args.append(a)

    def __init__(self,names):
        self._args=[];
        self.anyArg=None;
        self._names=names;

    def matches(self,name):
        return name in self._names;

    def toString(self):
        text="";
        for i in self._args:
            text+=i.toString();
        if (self.anyArg):
            text+=self.anyArg.toString()
        return self.id()+"("+text+")"

    def process(self,tokens):
        ns=set()
        for t in tokens:
            if (t.dep!=441):
                ns.add(t);
        tokens=ns;
        for a in self._args:
            a.consume(tokens);
        if (self.anyArg):
            if (len(tokens)==1):
                self.anyArg.consume(tokens)
        print tokens

class Verb:

    def id(self):
        return self._names[0]

    def __init__(self,names):
        self._actions=[];
        self._names=names;
        self.selected=False;

    def matches(self,name):
        return name in self._names

    def addAction(self,a):
        self._actions.append(a);
        a._verb=self;

    def dumpState(self):
        print self.selected.toString();

    def matchToken(self,t):
        args=set();
        selected=None
        if (self.matches(t.text)):
            for r in t.rights:
                if (r.dep==412):
                    for a in self._actions:
                        if (a.matches(r.text)):
                           for l in r.children:
                               if (l.head==r):
                                 args.add(l)
                           selected=a;
                else:
                    args.add(r);
            if (selected):
                a.process(args);
                self.selected=selected;
                return selected
        return None
class Universe:
  def __init__(self):
      self.verbs=[]



  def action(self,action):
      ac=action.split(" ");
      verb=None
      for v in self.verbs:
        if (v.id==ac[0]):
            verb=v;
            break
      if (verb==None):
          verb=Verb([ac[0]]);
          self.verbs.append(verb);
      action=None
      for a in verb._actions:
          if (ac[1] in a._names):
              action=a
      if (not action):
          action=Action([ac[1]]);
          verb.addAction(action)
      return action


  def add(self,v):
      if (v is Verb):
        self.verbs.append(v);

  def process(self,phrase):
      ps=nlp(phrase);
      rs=None
      for v in ps:
         if (v.head==v):
            for vr in self.verbs:
                rs=vr.matchToken(v);
                if rs:
                    break
      return rs;
u=Universe();


#vr=Verb(["create","open","new","add"]);
ac=u.action("create issue")
ac.addArg(Argument('priority'))
ac.addAnyArg(Argument("summary"))
#vr.addAction(ac)
#print v.matches("open")
#ps=nlp(u'create high priority issue buy milk for Ann')
#ps=nlp(u'open issue ')

vr=u.process(u"create issue - by milk; high priority; M4");
print(vr.toString());
