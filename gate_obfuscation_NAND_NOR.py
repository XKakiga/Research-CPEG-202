import argparse
import re
import networkx as nx
import random
import time
import os
 
 
 
 
def count_total_gates(bench):
    find_gates_all = re.compile(r"\S+\W*=\W*\S+\(.+?\)",re.DOTALL)
    gates_all = find_gates_all.findall(bench)
    num_total_gates = len(gates_all)
 
    return num_total_gates
 
 
def find_in_nets(line):
    find_in_net = re.compile(r"\(.+?\)",re.DOTALL)
    in_nets = find_in_net.findall(line)
    in_nets = in_nets[0].replace("(","").replace(")","").replace(" ","")
    in_nets = in_nets.split(",")
    return in_nets
 
def find_out_net(line):
    find_out_net = re.compile("\S+\W*=")
    out_net = find_out_net.findall(line)
    out_net = out_net[0].replace(" ","").replace("=","")
    return out_net
 
def find_primary_inp(bench):
    find_prim_in = re.compile("INPUT\(.+?\)")
    priminps = find_prim_in.findall(bench)
    return priminps
 
def find_primary_out(bench):
    find_prim_out = re.compile("OUTPUT\(.+?\)")
    primouts = find_prim_out.findall(bench)
    return primouts
   
def find_gates(bench):
    find_gates_all = re.compile(r"\S+\W*=\W*\S+\(.+?\)",re.DOTALL)
    gates_all = find_gates_all.findall(bench)
    return gates_all    
 
def find_gate_type(line):
    find_gate_type = re.compile(r"=\W*\S+\(")
    gate_type = find_gate_type.findall(line)
    gate_type = gate_type[0].replace("=","").replace(" ","").replace("(","")
   
    return gate_type
 
 
def create_graph(bench,count_check):
    G = nx.DiGraph()
    priminps = find_primary_inp(bench)
    prim_input = [s.replace(')',"").replace('INPUT',"").replace("(","").replace("\n","").replace("\t","") for s in priminps]
    primout = find_primary_out(bench)
    prim_output = [s.replace(')',"").replace('OUTPUT',"").replace("(","").replace("\n","").replace("\t","") for s in primout]
    gates_all = find_gates(bench)
    node_count = count_check
    node_name = []
    gate_name = []
    gate_define = []
    node_type = []
    gate_out_nets = []
 
    for inn in prim_input:
        if(inn == "zero_pin"):
            node_type.append("zero")
        elif(inn == "one_pin"):
            node_type.append("one")
        else:
            node_type.append("PI")
        node_name.append(str(node_count))
        node_count = node_count + 1
        gate_out_nets.append('none')
        gate_name.append(inn)
        gate_define.append(inn)
 
    for out in prim_output:
        node_type.append("PO")
        node_name.append(str(node_count))
        node_count = node_count + 1
        gate_out_nets.append('none')
        gate_name.append(out)
        gate_define.append(out)
 
    for gate_def in gates_all:
        gate_type = find_gate_type(gate_def)
        node_type.append(gate_type)
        node_name.append(str(node_count))
        gate_out_net = find_out_net(gate_def)
        gate_out_nets.append(gate_out_net)  
        node_count = node_count + 1
        gate_name.append(gate_type)
        gate_define.append(gate_def)    
 
 
         
    set_in = []
    for gate_def in gates_all:    
        net_out = find_out_net(gate_def)
        index = gate_out_nets.index(net_out)
        gate1 = node_name[index]
        nets_in = find_in_nets(gate_def)
        for inp in nets_in:
            if inp in prim_input:
                #print(inp)
                set_in.append(inp)
                index = gate_name.index(inp)
                G.add_edge(node_name[index],gate1)
           
            else:
                index = gate_out_nets.index(inp)
                G.add_edge(node_name[index],gate1)
       
        if (net_out in prim_output):
           
            index = gate_name.index(net_out)
            G.add_edge(gate1,node_name[index])
 
        '''  
             
        for gate2_def in gates_all:
            net2_out = find_out_net(gate2_def)
            index = gate_out_nets.index(net2_out)
            gate2 = node_name[index]
            nets2_in = find_in_nets(gate2_def)
            for innet in nets2_in:
                if (net_out == innet):
                    #print("yes")
                    G.add_edge(gate1,gate2)
        '''
                   
           
    orig_nodes = list(G.nodes)
       
    count_check = count_check + len(orig_nodes)
 
    return G,node_type,node_name,gate_define,gate_out_nets,orig_nodes,count_check
 
    #changed code
 
def lock_bench(bench, gate_ob, ntype, finalkey, gate_out_net, key_count):
    in_nets = find_in_nets(gate_ob)
    mux_str = ""
 
    if ntype == 'NAND' or ntype == 'NOR':
        # Obfuscate using NAND and NOR gates
        mux_str += f"{gate_out_net}_ob1 = NAND({','.join(in_nets)})\n"
        mux_str += f"{gate_out_net}_ob2 = NOR({','.join(in_nets)})\n"
 
        # Create a MUX to select between the obfuscated gates
        mux_str += f"{gate_out_net} = MUX(keyinput{key_count}, {gate_out_net}_ob1, {gate_out_net}_ob2)\n"
 
        # Determine the key bit based on the gate type
        # '0' for NAND, '1' for NOR
        key_bit = "0" if ntype == 'NAND' else "1"
        finalkey += key_bit
        key_count += 1
 
    else:
        # If the gate type is not NAND or NOR, leave it unchanged
        mux_str = f"{gate_out_net} = {ntype}({','.join(in_nets)})\n"
 
    # Regular expression pattern to find the specific gate definition
    gate_def_pattern = re.escape(gate_out_net) + r"\s*=\s*" + re.escape(ntype) + r"\(.*?\)"
    bench_lock = re.sub(gate_def_pattern, mux_str.strip(), bench, count=1, flags=re.DOTALL)
 
    return finalkey, key_count, bench_lock
 
def Gate_obfuscation(bench,pol,dataset_type,inputfile,count_check):
   
    G,node_type,node_name,gate_define,gate_out_nets,orig_nodes,count_check_add = create_graph(bench,count_check)
 
    OG = G.copy()
    OG_mod = G.copy()
    finalkey = ""
    bench_copy = bench
    dataset = ""
    num_origgates = count_total_gates(bench)
    print("orig_gates")
    print(num_origgates)
    num_obgates =  int((int(pol)/100)*(num_origgates))
    obgates = []
    print("number")
    print(num_obgates)
    key_count = 0
    type_file = dataset_type
    bench_lock = bench
   
    while(len(obgates) < num_obgates):
        flag = 0  
        while(flag == 0):
            n = random.randint(0,len(list(G.nodes))-1)
            node = list(G.nodes)[n]
            index =  node_name.index(node)
            ntype = node_type[index]
            if (ntype != "PO"):
                if(ntype != "PI"):
                    if(str(node) not in obgates):
                        #print("flag")
                       # if(ntype == "BUF") or (ntype =="NOT"):
                           
                        obgate = str(node)
                        obgates.append(obgate)
                        flag = 1
       
   
        index =  node_name.index(obgate)
        gate_ob = gate_define[index]
        out_net = gate_out_nets[index]
   
        finalkey,key_count,bench_lock = lock_bench(bench_lock,gate_ob,ntype,finalkey,out_net,key_count)
        bench_copy = bench_copy.replace(gate_ob,gate_ob.replace(ntype+"("," ("))
        dataset = dataset + out_net + " " + ntype + "\n"
       
 
    return bench_lock,count_check_add,finalkey,bench_copy,dataset    
 
   
 
def main(input_path,lock_path,pol,input_files,obs_path,dataset_dir):
    start = time.time()
    count_check_add = 0
    input_files = input_files.split(',')
    for file in input_files:
        with open(input_path+"/"+file,'r') as f:
             bench_file = f.read()
        print(count_check_add)
        count_check = count_check_add
       
        bench_locked,count_check_add,finalkey,bench_obs,dataset = Gate_obfuscation(bench_file,pol,file.replace(".bench",""),file,count_check)
        keyin = ""
        for t in range(len(finalkey)):
            keyin = keyin + "INPUT(keyinput"+str(t)+")\n"
        with open(obs_path+"/obfuscated_"+file,'w') as f:
             f.write(bench_obs)
        with open(dataset_dir+"/orig_obgates_"+file.replace(".bench",".txt"),'w') as f:
             f.write(dataset)
 
        with open(lock_path+"/locked_"+file,'w') as f:
             f.write("#key="+finalkey + "\n"+keyin+bench_locked)
        os.system("./lcmp "+input_path+"/"+file + " "+lock_path+"/locked_"+file + " key="+finalkey)
    end = time.time()
    print("time taken ")
    print(end-start)  
 
   
if __name__ == "__main__":
 
    parser = argparse.ArgumentParser(description='Gate Obfuscation of the bench file')
    parser.add_argument('--input_path', help='Path for input files')
    parser.add_argument('--lockout',help = 'Path for locked file')
    parser.add_argument('--obsout',help = 'path for obfuscated files')
    parser.add_argument('--percent', help='Percentage of obfuscation')
    parser.add_argument('--dataset_dir', help= 'Dataset directory')
    parser.add_argument('--test_files', help= 'Name of file to obfuscate')
    args = parser.parse_args()
 
    main(args.input_path,args.lockout,args.percent,args.test_files,args.obsout,args.dataset_dir)
