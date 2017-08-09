import yaml
with open('/Users/kor/git/aml/examples/aiva/lib/py/lib/definition.yaml') as f:
    # use safe_load instead load
    dataMap = yaml.safe_load(f)
    for v in dataMap:
        print dataMap[v]