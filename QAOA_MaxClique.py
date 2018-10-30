import qiskit
import numpy as np
import matplotlib.pyplot as plt
import json
from graph import *

P = 1;

def makeCircuit(inbits, outbits):
    q = qiskit.QuantumRegister(inbits+outbits)
    c = qiskit.ClassicalRegister(inbits+outbits)
    qc = qiskit.QuantumCircuit(q, c)

    q_input = [q[i] for i in range(outbits,outbits+inbits)]  # grover registers
    q_output = [q[j] for j in range(outbits)]                   # ancilla initialized to |->

    return qc, c, q_input, q_output

# measure all qubits in q_input register, return dictionary of samples
def measureInput(qc, q_input, c):
    for i in range(len(q_input)):
        qc.measure(q_input[i], c[i])
    job = qiskit.execute(qc, backend='local_qasm_simulator', shots=1024)
    return job.result().get_counts(qc)

def test5(qc, q_input, c):
    data = measureInput(qc, q_input, c)
    # assemble data from dictionary into list
    parsed = []
    xticks = []
    n = len(q_input)
    for i in range(2**n):
        bits = np.binary_repr(i, width=n)
        xticks.append(bits)
        if bits in data: parsed.append(data[bits])
        else: parsed.append(0)

    plt.bar(range(2**n), parsed)
    plt.xticks(range(2**n),xticks,rotation="vertical")
    plt.xlabel('Outcomes')
    plt.ylabel('Counts')
    plt.title('Measurement Histogram')
    plt.show()

def applyQAOA(gamma, beta, graph):
    ### INIT REGS
    qc, c, q_input, q_output = makeCircuit(graph.getNumNodes(), 1);
    PENALTY = int(graph.getMaxEdges())
    ### H on every input register
    for node in q_input:
        qc.h(node)
    complement = graph.getEdgesComp();
    edges = graph.getEdges()
    ### APPLY V AND W
    for i in range(P):
        ### APPLY V
        # EDGES IN THE GRAPH
        for edge in edges:
            nodeList = edge.getNodes()
            qc.cu1(-gamma, q_input[nodeList[0].name], q_input[nodeList[1].name])
        # EDGES NOT IN THE GRAPH
        for edge in complement:
            nodeList = edge.getNodes()
            qc.cu1(PENALTY*gamma, q_input[nodeList[0].name], q_input[nodeList[1].name])
            
        ### APPLY W
        for node in q_input:
            qc.h(node)
            qc.u1(2*beta, node)
            qc.h(node)

    ### Measure
    results = measureInput(qc, q_input, c)
    ### Compute the result expectation
    

    ### Parse the result list.
    # B/c we only care about counts associated with input register
    # we combine the counts of states with same input register bits
    
    counts = dict()
    for key in results:
        if key[1:] not in counts:
            counts[key[1:]] = results[key]
        else:
            counts[key[1:]] += results[key] 
    print(counts)
    expectation = 0
    for val in counts:
        cliqNum = 0
        #print("Edges:", len(edges))
        #print("Complement:", len(complement))
        for edge in edges:
            nodeList = edge.getNodes()
            #print("Node 1:", nodeList[0].name,"Node 2:", nodeList[1].name)
            if val[nodeList[0].name] == '1' and val[nodeList[1].name] == '1':
                cliqNum += 1
        for edge in complement:
            nodeList = edge.getNodes()
            if val[nodeList[0].name] == '1' and val[nodeList[1].name] == '1':
                cliqNum -= PENALTY
        
        print("cliq size", cliqNum)
        numNodesInCliq = cliqNum
        expectation += counts[val]/1024 * cliqNum
    #print("1110:", counts['1110'], "and 1011:", counts['1011'])
    return expectation



def gradient(func, params, epsilon, whichParam):
    first = params
    second = params
    first[whichParam] += epsilon
    second[whichParam] -= epsilon
    return func(*first) - func(*second)/(2*epsilon)

### gradient ascent optimizer
# graph is graph to optimize over
# epsilon controls how far out the delta is calculated
# eta is learning rate
# threshold is the average of gamma and beta that we will consider a max

def optimize(graph, epsilon, eta, threshold):
    count = 0
    gamma = 2
    beta = 2
    dgamma = (applyQAOA(gamma + epsilon, beta, graph) - applyQAOA(gamma - epsilon, beta, graph))/(2*epsilon)
    dbeta = (applyQAOA(gamma, beta + epsilon, graph) - applyQAOA(gamma, beta + epsilon, graph))/(2*epsilon)
    flipper = True #Alternate between maxing gamma and maxing beta
    while((abs(dgamma) + abs(dbeta))/2 > threshold):
        if(flipper):
            gamma += (dgamma/abs(dgamma) * dgamma * eta) % (2*np.pi)
            dgamma = (applyQAOA(gamma + epsilon, beta, graph) - applyQAOA(gamma - epsilon, beta, graph))/(2*epsilon)
        else:
            beta += (dbeta/abs(dbeta) * dbeta * eta) % np.pi
            dbeta = (applyQAOA(gamma, beta + epsilon, graph) - applyQAOA(gamma, beta + epsilon, graph))/(2*epsilon)
            
        count+=1
        flipper = not flipper
    
    print(count)
    return gamma, beta
    
def main():
    ### If P > 0
    #gamma = []
    #beta = []
    #   
    #for i in range(P):
    #    gamma.append(np.random.uniform(0,2*np.pi))
    #for i in range(P):
    #    beta.append(np.random.uniform(0,np.pi))


    
    ###TESTING GRAPH
    myGraph = Graph(0, 0)
    nodes = [Node(i) for i in range(4)]

    edges = []
    edges.append(Edge(nodes[0], nodes[1]))
    edges.append(Edge(nodes[1], nodes[2]))
    edges.append(Edge(nodes[2], nodes[3]))
    edges.append(Edge(nodes[3], nodes[0]))
    edges.append(Edge(nodes[3], nodes[1]))

    for n in nodes:
        myGraph.addNode(n)
    
    for e in edges:
        myGraph.addEdge(e)

        
    ### Run the algorithm
    #expect = applyQAOA(gamma, beta, myGraph)
    #print("Expectation Value:", expect)

    ### OPTIMIZE
    #bestGamma, bestBeta = optimize(myGraph, 0.1, 0.1, 0.05)
    # Optimal Gamma: 3.10693359375 Optimal Beta: 2.50830078125
    # This is very likely a local max though.
    # We might want optimize from various start positions and compare results
    # Also need to discuss optimization parameters cause I kind of chose those arbitrarily
    """
    Hi this is a block Comment
    """
    print("Optimized Expectation value", applyQAOA(3.10693359375, 2.50830078125, myGraph))
    #print("Optimal Gamma:", bestGamma, "Optimal Beta:", bestBeta)

    ### Make graphs.
    # I'm thinking we hold one variable constant at its maxed value
    # and vary the other and vice versa.
    # Gamma has a larger range than beta. Do we want more data points for gamma than beta?
    # The last page of the worksheet says exactly which graphs we need in our report
    # so make sure we have at least those
    """gamma = 3.10693359375
    beta = 2.50830078125
    betas = np.linspace(0, np.pi, 100)
    gammas = np.linspace(0, 2*np.pi, 100)
    varyingBeta = []
    varyingGamma = []
    
    y = [applyQAOA(gammaa, beta, myGraph) for gammaa in gammas]
    with open("varyingGamma.txt", 'w') as f:
        json.dump(y, f)
        
    y = [applyQAOA(gamma, betaa, myGraph) for betaa in betas]
    with open("varyingBeta.txt", 'w') as f:
        json.dump(y, f)
     """   
    #with open("varyingGamma.txt", 'r') as f:
    #    varyingGamma = json.load(f)
    
    #with open("varyingBeta.txt", 'r') as f:
    #   varyingBeta = json.load(f)

    #betaG = plt.plot(betas, varyingBeta)
    #gammaG = plt.plot(gammas, varyingGamma)
    #plt.legend(('Beta Graph', 'Gamma Graph'))
    #plt.xlabel('Beta and Gamma values')
    #plt.ylabel('Expectation Value')
    #plt.title('Expectation Value vs Gamma and Beta')
    #plt.show()
    
    
main()
