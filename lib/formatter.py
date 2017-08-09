# This Python file uses the following encoding: utf-8
MAX_ITEMS=30;
def format(res):
    result=""
    num=0;
    if (not isinstance(res,list) and not isinstance(res,set)):
        result=str(res)
        return "Single thing:"+result;
    if (len(res)==0):
        return "Nothing found"
    for i in res:
        try:
            vl=str(i);
            if (i.url):
                result=result+u"• "+"<"+i.url+"|"+vl+">\n";
            else: result=result+(u"• "+unicode(vl)).encode("utf-8")+"\n"
        except:
            result=result+(u"• Can not encode item".encode("utf-8"))+"\n"
        num=num+1;
        if (num>MAX_ITEMS):
            result+="Printed first 30 results of:"+str(len(res))+", ask more to get more"
            break;
    return result;
w=""
