import shlex;
class Or:
    def __init__(self,options):
        self.options=options;
    def __call__(self, *args, **kwargs):
        res=set()
        for option in self.options:
            if (callable(option)):
                result=option(args[0]);
                for v in result:
                    res.add(v);
            else:
                for v in args[0]:
                    if (v==option):
                        res.add(v)
        return res;
    def __repr__(self):
        return self.__str__()
    def __str__(self):
        if len(self.options)==1:
            return str(self.options[0]);
        return "or"+str(self.options);

class And:
    def __init__(self,options):
        self.options=options;
    def __repr__(self):
        return self.__str__()
    def __str__(self):
        if len(self.options) == 1:
            return str(self.options[0]);
        return "and" + str(self.options);
    def __call__(self, *args, **kwargs):
        res=None;
        for option in self.options:
            result=option(args[0]);
            if (res==None): res=result;
            else:
                res=res.intersect(result);
        return res;
class Not:
    def __init__(self,options):
        self.options=options;
    def __repr__(self):
        return self.__str__()
    def __str__(self):
        return "not " + str(self.options);
    def __call__(self, *args, **kwargs):
        result=self.options(args[0]);
        if (len(result)>0 or result==True):
            return False;
        return True;
class CountCompare:
    def __init__(self,options,op):
        self.options=options;
        self.op=op;
    def __repr__(self):
        return self.__str__()
    def __str__(self):
        return " count "+self.op+" " + str(self.options);
    def __call__(self, *args, **kwargs):
        result=self.options(args[0]);
        if (len(result)>0 or result==True):
            return False;
        return True;
class Flow:
    def __repr__(self):
        return self.__str__()

    def __str__(self):
        if len(self.chain) == 1:
            return str(self.chain[0]);
        res=""
        for i in range(0,len(self.chain)):
            res=res+str(self.chain[i]);
            if (i<len(self.chain)-1):
                res=res+"=>";
        return res;
    def __init__(self,*args):
        if (len(args)==1):
            self.chain=args[0];
        else:
            self.chain=args;
    def __call__(self, *args, **kwargs):
        v=args[0];
        for op in self.chain:
            v=op(v);
        return v;
class Eq:
    def __init__(self,val):
        self.val=val;
    def __call__(self, *args, **kwargs):
        res=set();
        for v in args[0]:
            if (v==self.val): res.add(v);
        return res;
class ParentValueFilter:
    def __init__(self,val):
        self.val=val;
    def __call__(self, *args, **kwargs):
        res=set();
        for v in args[0]:
            if (v==self.val): res.add(v);
        return res;

    def __repr__(self):
        return self.__str__()


    def __str__(self):
        return "parent("+str(self.val)+")"
class CountInstances:
    def __init__(self,toCount):
        self.toCount=toCount
    def __repr__(self):
        return self.__str__()

    def __str__(self):
            return "count("+str(self.toCount)+")"
class SelectInstances:
    def __init__(self,class_name):
        self.class_name=class_name;

    def __repr__(self):
        return self.__str__()

    def __str__(self):
            return "select("+self.class_name+")"
class FilterByVals:
    def __init__(self,vals):
        self.vals=vals;

    def __repr__(self):
        return self.__str__()

    def __str__(self):
            return " in ("+str(self.vals)+")"
class FilterPropertyValue:
    def __init__(self,pn,pred):
        self.pn=pn;
        self.pred=pred;

    def __repr__(self):
            return self.__str__()
    def __str__(self):
        if (callable(self.pred)):
            return self.pn+str(self.pred)
        return self.pn+'=='+str(self.pred);
    def __call__(self, *args, **kwargs):
        res=set();
        for v in args[0]:
            if (callable(self.pred)):
                am=self.pred([v[self.pn]])
                if (len(am)>0):
                    res.add(v);
            else:
                if v[self.pn]==self.pred:
                    res.add(v)
                if (isinstance(self.pred,list)):
                    for q in self.pred:
                        if (v[self.pn]==q):
                            res.add(v)
        return res;
class Count:
    def __init__(self,pred):
        self.pred=pred;
    def __call__(self, *args, **kwargs):
        return len(self.pred(args[0]));
class TakePropertyValue:
    def __init__(self,pred,pn):
        self.pn=pn;
        self.pred=pred;
    def __call__(self, *args, **kwargs):
        res=list();
        rr=self.pred(args[0]);
        for v in rr:
            res.append(v[self.pn])
        return res;
    def __repr__(self):
        return self.__str__()

    def __str__(self):
         return str(self.pred)+"["+self.pn+"]"

class instance:
    def __init__(self,data):
        self.data=data;
    def __hash__(self):
        return self.data['name'].__hash__();
    def __getitem__(self, item):
        return self.data[item];
    def __str__(self):
        return self['name']
    def __repr__(self):
        return str(self)

