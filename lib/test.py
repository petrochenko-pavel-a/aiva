# This Python file uses the following encoding: utf-8
import Collector
import vocabulary
import formatter
#print "•"
voc=vocabulary.Vocabulary('/Users/kor/git/aml/examples/aiva/lib/py/lib/definition.yaml')
defs=Collector.Definifion('/Users/kor/git/aml/examples/aiva/lib/py/lib/api.yaml',voc,load=True)
defs.load("Organization",{"id":"raml-org"})
#
query=defs.query("open issues created by Christian and assigned to Konstantin");
print query
q=defs.executeQuery("open issues created by Christian and assigned to Konstantin")
#print q
print formatter.format(q)
#print q

