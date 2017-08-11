import unittest
import grammar_parser as gp;

class TestParse(unittest.TestCase):

    def test_basic(self):
        compare("created_by gleb","[filter:created_by==gleb]")
        compare("created_by gleb and assigned_to denis","[filter:and[created_by==gleb, assigned_to==denis]]")
        compare("created_by gleb assigned_to denis", "[filter:and[created_by==gleb, assigned_to==denis]]")
        compare("created_by gleb assigned_to denis  in raml-js-parser-2", "[filter:and[created_by==gleb, assigned_to==denis, parent(raml-js-parser-2)]]")
        compare("issues", "[selector:select(issue)]")
        compare("issues created_by gleb", "[selector:select(issue)=>created_by==gleb]")
        compare("issues created_by gleb or denis", "[selector:select(issue)=>created_by==['gleb', 'denis']]")
        compare("issues created_by gleb or denis in raml-js-parser-2", "[selector:select(issue)=>and[created_by==['gleb', 'denis'], parent(raml-js-parser-2)]]")
        compare("issues created_by gleb and not assigned_to denis in raml-js-parser-2", "[selector:select(issue)=>and[created_by==gleb, not assigned_to==denis, parent(raml-js-parser-2)]]")
        compare("created more then 5 issues", "[filter:created count > 5=> in (select(issue))]")
        compare("users created more then 5 issues", "[selector:select(user)=>created count > 5=> in (select(issue))]")
        compare("labels of issues created_by gleb", "[selector:select(issue)=>created_by==gleb[labels]]")
        compare("raml-js-parser-2 owner", "[selector:raml-js-parser-2[owner]]")
        compare("count issues in raml-js-parser-2", "[count:count(select(issue)=>parent(raml-js-parser-2))]")
        compare("users created more issues then denis", "[filter:select(user)[created]=> in (select(issue))=> count > count(denis[created]=> in (select(issue)))]")
        compare("users created more issues then denis created in raml-js-parser-2", "[filter:select(user)[created]=> in (select(issue))=> count > count(denis=>createdparent(raml-js-parser-2)[created]=> in (select(issue)))]")
        compare2("issues created_by2 users created more then 5 issues","")
    #def test_nested(self):
        #compare2("issues created by users with assigned issues")
if __name__ == '__main__':
    unittest.main()

tm={

    "gleb":("selector","gleb"),
    "raml-js-parser-2":("selector","raml-js-parser-2"),
    "denis":("selector","denis"),
    "repositories":("cn","repository"),
    "issues":("cn","issue"),
    "users":("cn","user"),
    "labels":("pn","labels"),
    "owner":("pn","owner"),
    "them": ("val", "them"),
    "assigned_to":("pn","assigned_to"),
    "created_by":("pn","created_by"),
    "created":("pn","created")
}
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
def tokenize(s):
    res=[]
    for k in s.split():
        if (k in tm):
            res.append(tm[k]);
        else:
            if (is_number(k)):
                res.append(("selector", k))
            else: res.append(("str",k))
    return res;

def compare(tp,s):
    if (not s==str(parse(tp))):
        print  parse(tp)
    assert s==str(parse(tp))
def compare2(tp,s):
    gp.debug=True;
    print  parse(tp)
    gp.debug = False;
    assert s==str(parse(tp))

def parse(s):
    vv=tokenize(s)
    return gp.parse(gp.tokens(vv));