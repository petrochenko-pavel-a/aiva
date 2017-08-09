import shlex;
class Or:
    def __init__(self,*options):
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
class And:
    def __init__(self,*options):
        self.options=options;
    def __call__(self, *args, **kwargs):
        res=None;
        for option in self.options:
            result=option(args[0]);
            if (res==None): res=result;
            else:
                res=res.intersect(result);
        return res;
class Flow:
    def __init__(self,chain):
        self.chain=chain;
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

class FilterPropertyValue:
    def __init__(self,pn,pred):
        self.pn=pn;
        self.pred=pred;
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

