import os
import numpy
import itertools
import re
import simplejson as json
from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Q
from django.core.mail import send_mail
from models import Disease
from termDict import termIndices # dictionary for index of disease terms

def navigation_autocomplete(request,
    template_name='autocomplete.html'):

    q = request.GET.get('q', '')
    context = {'q': q}

    queries = {}
    queries['concepts'] = Disease.objects.filter(
        Q(concept__icontains=q) |
        Q(synonyms__icontains=q)
    ).distinct()[:20]

    context.update(queries)

    return render(request, template_name, context)

def createJSON(term, method, nodes):
    # Find index of searched term
    termIndex = termIndices[term]

    # Load citation freq matrix based on method, create submatrix base on node num
    if method == 'cooccurrence':
        matFile_path = os.path.join(os.path.dirname(__file__),'data','diseaseWithPsychCitationGMStat.npy')
    elif method == 'similarity':
        matFile_path = os.path.join(os.path.dirname(__file__),'data','diseaseWithPsychCitationCosine.npy')
    else:
        matFile_path = ''
    cFreqMat = numpy.load(matFile_path,'r')
    cFreqMat_row = cFreqMat[termIndex,:]
    nodesIndicesSorted = numpy.argsort(cFreqMat_row, kind='mergesort')

    nodesIndicesSorted = nodesIndicesSorted[::-1]
    nodesIndicesTop = nodesIndicesSorted[1:nodes+1]

    # Load xml file of MeSH diseases
    import xml.etree.ElementTree as ET
    dxList_tree = ET.parse(os.path.join(os.path.dirname(__file__),'data','diseaseListWithPsychEss.xml'))
    dxList_root = dxList_tree.getroot()

    '''# Running list of tree numbers
    treeNumList = []
    disease = dxList_root.find('.//*[@indexnum="%d"]' % termIndex) # add tree numbers of primary disease
    for treenumPrimary in disease.findall('TreeNumberList/TreeNumber'):
        treeNumList.append(treenumPrimary.text)

    # Retrieve top nodes based on link strength, preclude all nodes which are in a parent or child class
    nodesIndicesTop = []
    count = 0
    pos = nodesIndicesSorted.shape[0]-2 # The top value will be the singular frequency of term, start with pairwise frequencies
    while (count < nodes):
        disease = dxList_root.find('.//*[@indexnum="%d"]' % nodesIndicesSorted[pos])
        parentClass = False
        for treenumA in disease.findall('TreeNumberList/TreeNumber'):
            for treenumB in treeNumList:
                if (treenumA.text in treenumB) or (treenumB in treenumA.text):
                    parentClass = True
        if not parentClass:
            nodesIndicesTop.append(nodesIndicesSorted[pos])
            for treenumA in disease.findall('TreeNumberList/TreeNumber'):
                treeNumList.append(treenumA.text)
            count += 1
            pos -= 1
        else:
            pos -= 1'''

    # Form sub-matrix based on list of top nodes
    nodesIndices = numpy.insert(nodesIndicesTop,0,termIndex)
    cFreqMat_reduced = cFreqMat[nodesIndices,:][:,nodesIndices]

    '''# Convert submatrix into json data variable, pass to template
    jsondata = '{"nodes":['
    for k in range(nodes+1):
        disease = dxList_root.find('.//*[@indexnum="%d"]' % nodesIndices[k])
        # re.escape escapes special characters, especially apostrophes, which cause problems as javascript variable
        node_jsonEntry = '{"name":"%s",' % re.escape(disease.find('Name').text)
        node_jsonEntry = node_jsonEntry + '"size":%d,' % cFreqMat_reduced[k,k]
        node_jsonEntry = node_jsonEntry + '"group":['
        if k==0:
            catnum = 0
            catname = 'primary'
            node_jsonEntry = node_jsonEntry + '{"groupnum":%d,' % catnum
            node_jsonEntry = node_jsonEntry + '"groupname":"%s"},' % catname
        else:
            for cat in disease.findall('CatList/Category'):
                catnum = int(cat.find('CatNum').text)
                catname = cat.find('CatName').text
                node_jsonEntry = node_jsonEntry + '{"groupnum":%d,' % catnum
                node_jsonEntry = node_jsonEntry + '"groupname":"%s"},' % catname
        node_jsonEntry = node_jsonEntry[:-1]
        node_jsonEntry = node_jsonEntry + ']},'
        jsondata = jsondata + node_jsonEntry
    jsondata = jsondata[:-1]
    jsondata = jsondata + '], "links":['
    for m, n in itertools.combinations(range(nodes+1), 2):
        link_jsonEntry = '{"source":%d,' % m
        link_jsonEntry = link_jsonEntry + '"target":%d,' % n
        link_jsonEntry = link_jsonEntry + '"coefficient":%f},' % cFreqMat_reduced[m,n]
        jsondata = jsondata + link_jsonEntry
    jsondata = jsondata[:-1]
    jsondata = jsondata + ']}'
    return jsondata'''

    nodes_array = []
    links_array = []
    for k in range(nodes+1):
        disease = dxList_root.find('.//*[@indexnum="%d"]' % nodesIndices[k])
        node_groupArray = []
        if k==0:
            catnum = 0
            catname = "primary"
            node_groupArray.append({"groupnum": catnum, "groupname": catname})
        else:
            for cat in disease.findall('CatList/Category'):
                catnum = int(cat.find('CatNum').text)
                catname = cat.find('CatName').text
                node_groupArray.append({"groupnum": catnum, "groupname": catname})
        nodes_array.append({"name": disease.find('Name').text, "size": numpy.asscalar(cFreqMat_reduced[k,k]), "group": node_groupArray})
    for m, n in itertools.combinations(range(nodes+1), 2):
        links_array.append({"source": m, "target": n, "coefficient": numpy.asscalar(cFreqMat_reduced[m,n])})
    data = {"nodes": nodes_array, "links": links_array}
    return data

def getJSONData(request):
    if request.is_ajax():
        try:
            term = request.GET['term']
            method = request.GET['method']
            nodes = int(request.GET['nodes'])
            data = createJSON(term, method, nodes)
        except Exception as e:
            print e
    else:
        data = 'fail'
    mimetype = 'application/json'
    return HttpResponse(json.dumps(data), mimetype)

# Request handler for graph button pressed
def graph(request):
    term = request.GET['q']
    method = request.GET['metric']
    nodes = int(request.GET['nodenum'])

    # Render page from template
    template_values = {
        'term': term,
        'method': method,
        'nodes': nodes,
        'keylabel': 'Key:',
        'graph': True}
    return render(request, 'index.html', template_values)

def index(request):
    term = 'Lupus Erythematosus, Systemic'
    method = 'cooccurrence'
    nodes = 15
    template_values = {
        'term': term,
        'method': method,
        'nodes': nodes,
        'keylabel': 'Key:',
        'graph': True}
    return render(request, 'index.html', template_values)

def contact(request):
    name = request.POST.get('f_name', None)
    email = request.POST.get('f_email', None)
    msg = request.POST.get('f_message', None)
    try:
        send_mail('DiseaseLink - message from user', name + '\n' + email + '\n\n' + msg, 'lchen3@gmail.com', ['lchen3@gmail.com'])
        return HttpResponse(status=200)
    except:
        return HttpResponse(status=500)
