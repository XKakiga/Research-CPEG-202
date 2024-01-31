export bench_name=b14_C_syn
export keysize=8
export specification=5pc_NAND_NOR
export p=5
 
mkdir -p results/${bench_name}/ # Create a results folder for locked_files
mkdir -p results/${bench_name}/temp # create a temp folder
 
for trial in $(seq 1 100)
do
    # Run the obfuscation script
    python3 gate_obfuscation_NAND_NOR.py --input_path ./BENCH/ --lockout ./results/${bench_name}/temp --percent ${p} --test_files b14_C_syn.bench --dataset_dir ./dataset/ --obsout ./obfuscated_files/
    export trial=$trial
    # Rename and move the locked file to the results folder with trial number
    locked_file="./results/${bench_name}/${bench_name}_${specification}_${trial}.bench"
    mv ./results/${bench_name}/temp/* $locked_file
    rm -rf ${bench_name}_obfuscation_k_${keysize}_${trial}.bench
 
    # Extract the key from the locked file
    key=$(grep '^#key' $locked_file | cut -d '=' -f2)
    
    #uses lcmp
    ./lcmp ./BENCH/b14_C_syn.bench $locked_file key=$key 
    
    
    #checks lcmp's result
    if [ $? -eq 0 ]; then
    	echo "lcmp has worked for trial $trial"
    else
    	echo "lcmp has failed for trial $trial"
    fi
 
    sleep 1
done

#This code obfuscates a given bench fil using the python code gate_obfuscation_NAND_NOR.py for 100 trials. Each trial gets checked using lcmp to make sure the secret key is working. 

#To use code change bench_name to file name, and specification to howeever you would like to describe the obfuscation done on the bench file. 

### Update - code changed and added p to make percentage customization easier. 
### Update - changed name to NAND_NOR_pc.sh


#Cedrick Casuga
