# -*- coding: utf-8 -*-
"""
Created on Sun Aug 27 13:44:13 2017

@author: akanksha
"""

# -*- coding: utf-8 -*-
"""
Created on Wed Apr 26 19:05:38 2017

@author: akanksha
"""

import argparse 
import numpy as np
import os
import glob
import subprocess 
import  itertools
import sys
import shutil
from collections import OrderedDict
import functools
import pandas as pd
import multiprocessing
import multiprocessing.pool
from HOME import HOME_timeseries_functions as ho

from os.path import join

def remEmptyDir(mypath):
    for root, dirs, files in os.walk(mypath,topdown=False):
         for name in dirs:
             fname = join(root,name)
             if not os.listdir(fname): #to check wither the dir is empty
                 
                 os.removedirs(fname)
def main(c):
    try: 
        df_path=[]
        sample_name_temp=[]
        for i in xrange(len(dictionary)):
            
            val=[]
            count=0
            d_rep={}
            input_file1=dictionary.values()[i]
            sample_name1=dictionary.keys()[i]
            sample_name_temp.append(sample_name1)
            
            for j in input_file1:
                
                count=count+1
                c1=["chr", "pos", "strand", "type", "mc"+"_rep"+str(count), "h"+"_rep"+str(count)]
                d_rep[count]=pd.read_table(j+'/'+c+'.tsv',header=None,names=c1)
                
            val.append(functools.reduce(merge, d_rep.values()))            
                
            df=functools.reduce(merge, val)
            df=df.sort_values(['pos'])
            df.to_csv(o.outputpath+'/temp_HOME/'+sample_name1+"_format_{c}.txt".format(c=c),header=True, index=False,sep='\t')    
            df_path.append(o.outputpath+'/temp_HOME/'+sample_name1+"_format_{c}.txt".format(c=c))  
        dictionary_new = OrderedDict(zip(sample_name_temp,df_path))
        result_list = map(OrderedDict, itertools.combinations(dictionary_new.iteritems(), 2))
        df4=[] 
        for iii in result_list:
     
            input_file1= iii[iii.keys()[0]]
            input_file2=iii[iii.keys()[1]]
            sample_name1=iii.keys()[0]
            sample_name2=iii.keys()[1]
            dfa=pd.read_table(str(input_file1),header=0)
            dfb=pd.read_table(str(input_file2),header=0)
            ra=dfa.shape[1]-4
            rb=dfb.shape[1]-4
    
            p_mc=3
            p_h=4
            for i in range(1,((ra)/2)+1):
                
                dfa.rename(columns={dfa.columns[i+p_mc]:"mc1_rep"+str(i)}, inplace = True)
                dfa.rename(columns={dfa.columns[i+p_h]:"h1"+"_rep"+str(i)}, inplace = True)
                p_mc=p_mc+1
                p_h=p_h+1
                
            p_mc=3
            p_h=4    
            for i in range(1,((rb)/2)+1):
               
                dfb.rename(columns={dfb.columns[i+p_mc]:"mc2"+"_rep"+str(i)}, inplace = True)
                dfb.rename(columns={dfb.columns[i+p_h]:"h2"+"_rep"+str(i)}, inplace = True)
                p_mc=p_mc+1
                p_h=p_h+1
      
            df = pd.merge(dfa, dfb, how='inner', on=['chr','pos',"strand","type"])
            df=df.sort_values(['pos'])
            df1=ho.format_allc(df, classes)
            del(df) 
    
            if min(numreps)>1 and max(numreps)>1:
           
                CHUNKSIZE = int(len(df1)/nop)
                CHUNKSIZE_list=[CHUNKSIZE]*nop 
                extra=(len(df1)%nop)
                
                if extra> 0:
                    
                    CHUNKSIZE_list[-1]=CHUNKSIZE_list[-1]+extra
                    
                df_chunk=ho.chunker1(df1,CHUNKSIZE_list)
                ttc=0
                df_path=[]
                
                for i in df_chunk:
                    
                    ttc=ttc+1
                    i.to_csv(o.outputpath+'/temp_HOME'+'/chunks/'+sample_name1+"VS"+sample_name2+"_df_{c}_{ttc}.txt".format(c=c,ttc=ttc),header=True, index=False,sep='\t')    
                    df_path.append(o.outputpath+'/temp_HOME'+'/chunks/'+sample_name1+"VS"+sample_name2+"_df_{c}_{ttc}.txt".format(c=c,ttc=ttc))
                   
                if nop>1:    
                    
                    pool = multiprocessing.Pool(processes=nop)
                    process = [pool.apply_async(ho.process_frame_withR, args=(dd,)) for dd in df_path]
                    pool.close()
                    pool.join()
                    
                    pool = multiprocessing.Pool(processes=nop)
                    process = [pool.apply_async(ho.pval_format_withrep, args=(dd,)) for dd in df_path]
                    pool.close()
                    pool.join()
    
                    output = [p.get() for p in process]
                    df3=pd.concat(output, ignore_index=True,axis=0)
    
                else:
    
                    ho.process_frame_withR(df_path[0])
                    df3=ho.pval_format_withrep(df_path[0])
                
                smooth_exp_val=ho.smoothing(*df3.exp_val) 
                df3['smooth_val']=(smooth_exp_val-min(smooth_exp_val))/(max(smooth_exp_val)-min(smooth_exp_val))
            
            else:
            
                df3=ho.pval_cal_withoutrep(df1)
       
            if classes=="CG":
    
                input_file_path=os.getcwd()+'/training_data/training_data_CG.txt'
                model_path=os.getcwd()+'/saved_model/CG/'
                k=ho.norm_slidingwin_predict_CG(df3,input_file_path,model_path)
                
            elif classes=="CHG" or classes=="CHH" or classes=="CHN" or classes=="CNN":
       
                input_file_path=os.getcwd()+'/training_data/training_data_nonCG.txt'
                
                model_path=os.getcwd()+'/saved_model/nonCG/'
                if nop>1:
                    CHUNKSIZE = int(len(df3)/nop)
                    df_chunk=ho.chunker(df3,CHUNKSIZE)
                    pool = multiprocessing.Pool(processes=nop)
                    
                    process = [pool.apply_async(ho.norm_slidingwin_predict_nonCG, args=(dd,input_file_path,model_path)) for dd in df_chunk]
                    
                    pool.close()
                    pool.join()
                    output = [p.get() for p in process]
                    k=pd.concat(output, ignore_index=True,axis=0)
                else:    
                    k=ho.norm_slidingwin_predict_nonCG_withoutchunk(df3,input_file_path,model_path)
      
            df4.append(k)
            
        for i, df in enumerate(df4, start=1):
                    df.rename(columns={col:'{}_df{}'.format(col, i) for col in ('glm_predicted_values', 'delta','win_sign')}, inplace=True)         
        merge1 = functools.partial(pd.merge, how='inner', on=['pos'])
        dfd=functools.reduce(merge1, df4) 
        
        filter_col = [col for col in list(dfd) if col.startswith(('glm'))]
        sum_val=dfd[filter_col].sum(axis=1)
        final_val=pd.concat([dfd.pos,sum_val], axis=1)
        final_val.columns=['pos','glm_predicted_values']
        
        dmrs=ho.clustandtrim(final_val,sc,minlen,mc)
          
        
        if len(dmrs)!=0:
            filter_col1= [col for col in list(dfd) if col.startswith(('win'))]
            filter_col2= [col for col in list(dfd) if col.startswith(('delta'))]
            scores=[]
            sign_win1=[]
            max_delta=[]
            for i in xrange(len(dmrs)):
                
                start=int(dmrs.start[i])
                stop=int(dmrs.end[i])
                val_index=dfd.index[(dfd.pos>=start) & (dfd.pos<=stop)].tolist()
                k=(max(dfd.iloc[val_index][filter_col].sum()))/dmrs.numC[i]
                max_delta.append(max( np.mean(abs(dfd.iloc[val_index][filter_col2]))))
                kk=max(0.2,(np.log(dmrs.numC[i])/np.log(dmrs.len[i])))
                
                scores.append((k*kk))
                val_sign=[]
                u=dfd.iloc[val_index][['pos']+filter_col]
                u=u.reset_index(drop=True) 
                u_full=dfd.iloc[val_index]
                u_full=u_full.reset_index(drop=True) 
                stop_df=0
                start_df=0
                for j in xrange(1,len(filter_col)+1):
                    win=False
                    for g in xrange(len(u)):
                        if u.iloc[g][j]>0.1:
                            if win==False:
                                start_df=u.iloc[g][0]
                                win=True
                        if win==True and u.iloc[g][j]<0.1:
                                stop_df=u.iloc[g-1][0]
                                break
                        if win==True and g==(len(u)-1) and u.iloc[g][j]>0.1: 
                            stop_df=u.iloc[g][0]
                    if start_df!=0 and stop_df!=0:
                        val_index1=u_full.index[(u_full.pos>=int(start_df)) & (u_full.pos<=int(stop_df))].tolist()
                        delta_df=np.mean(abs(u_full.iloc[val_index1][filter_col2]))
                        
                        dmr_sign=np.median(u_full.iloc[val_index1][filter_col1],axis=0)
                     
                        if dmr_sign[j-1]==-1.0:
                               
                               status_win="{start_df}:{stop_df}:hypo:{delta_df}".format(start_df=int(start_df),stop_df=int(stop_df),delta_df=round(delta_df[j-1],3))
                        elif dmr_sign[j-1]==1.0:
                               status_win="{start_df}:{stop_df}:hyper:{delta_df}".format(start_df=int(start_df),stop_df=int(stop_df),delta_df=round(delta_df[j-1],3))
                        
                        else:  
                                
                                status_win="NA" 
                    elif start_df==0 and stop_df==0: 
                        status_win="NA"         
                    val_sign.append(status_win)
                sign_win1.append(val_sign) 
            
            scores=pd.DataFrame(scores,columns=['confidence_scores'])
            max_delta=pd.DataFrame(max_delta,columns=['max_delta'])
            name_win=[]
            comb_samples=itertools.combinations(list(samplenames), 2)
            for i in comb_samples:
# 
                name_win.append(i[0]+"_VS_"+i[1])
            sign_win1=pd.DataFrame(sign_win1,columns=name_win)
            dmr_final=pd.concat([df1.chr[0:len(dmrs)],dmrs,max_delta,scores,sign_win1],axis=1)
            dmr_final=dmr_final[dmr_final.max_delta>=d]
            dmr_final=dmr_final.reset_index(drop=True)
            dmr_final['chr'] = dmr_final['chr'].astype(str)
            dmr_final.to_csv(o.outputpath+'/HOME_Timeseries_DMRs'+"/"+"Timeseries_HOME_DMR_{c}.txt".format(c=c),header=True, index=False,sep='\t')
            print "DMRs for {c} done".format(c=c)
            for filename in glob.glob(o.outputpath+'/temp_HOME'+"/df_{c}_*.txt".format(c=c)) :
                os.remove(filename)      
        return 
           
    except Exception as e:
        raise Exception(e.message)
#main code

## Inputs from user  
np.set_printoptions(threshold=np.inf,suppress=True,linewidth=np.inf,precision=3)
parser = argparse.ArgumentParser(description='HOME -- HISTOGRAM Of METHYLATION',formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-i','--samplefilepath', help='path of the sample file with samplename and sample path TAB seperated', required=True)
parser.add_argument('-t','--type', help='type of class', choices=["CG","CHG","CHH","CHN","CNN"],required=True, type=str)
parser.add_argument('-o','--outputpath', help='path where the DMRs will be saved', required=True)
parser.add_argument('-npp','--numprocess', help='number of process to be run at a time', required=False, type=int,default=10)
parser.add_argument('-sc','--scorecutoff',  help='min classifier score required to cluster the DMR',choices=np.arange(0,1,0.1), required=False, type=float,default=0.5)
parser.add_argument('-ml','--minlength', help='minimum length of DMRs to be reported', required=False, type=int,default=10)
parser.add_argument('-sin','--singlechrom',  help='parallel for single chromosomes',action='store_true',default=False)
parser.add_argument('-ns','--numsamples', help='number of samples to use for pairwise DMR calling', required=False, type=int)
parser.add_argument('-sp','--startposition', help='start position of samples to use for pairwise DMR calling', required=False, type=int)
parser.add_argument('-BSSeeker2','--BSSeeker2',  help='input CGmap file from BS-Seeker2',action='store_true',default=False)
parser.add_argument('-mc','--minc', help='minimum number of C in a DMR to reported', required=False, type=int,default=4)
parser.add_argument('-d','--delta', help='minimum average difference in methylation required', required=False, type=float,default=0.1)

if __name__ == "__main__":
    
    
    ## Read the inputs and preprocess the files 
    o=parser.parse_args()
    classes=o.type
    if o.startposition is not None:
        
        sp=(o.startposition)-1
    else:
        
        sp=0
        
    if o.numsamples is not None:
        
        ns=o.numsamples
    else:
        
        ns=len(o.samplefilepath)
        
    BSSeeker2=o.BSSeeker2
    df_file=pd.read_table(o.samplefilepath,header=None)
    samplenames=df_file.iloc[sp:sp+ns,0]
    samplenames.reset_index(drop=True,inplace=True)
    input_files=df_file.iloc[sp:sp+ns,1:]
    input_files.reset_index(drop=True,inplace=True)
    numreps=[len(input_files.ix[x].dropna()) for x in xrange (len(input_files))]
    
    input_files=[list(input_files.ix[x].dropna()) for x in xrange (len(input_files))]
    
    k=-1
    cwd = os.getcwd()
    
    
    if not os.path.exists((o.outputpath+'/temp_HOME')):
                os.makedirs(o.outputpath+'/temp_HOME')
    else: 
        print(" Temp directory at output path already exist.... please clean up and rerun")
        sys.exit()
                  
    input_files_mod=[]
    
    ## make output directory and store the input files per chromosome could be done in python but using awk as its faster 
    for i in input_files:
          temp_file=[]
          k=k+1
          for ii in xrange(len(i)):
              
         
              if not os.path.exists((o.outputpath+'/temp_HOME'+'/'+samplenames[k]+'_rep'+str(ii+1))):
                  
                  os.makedirs((o.outputpath+'/temp_HOME'+'/'+samplenames[k]+'_rep'+str(ii+1)))
                  os.chdir((o.outputpath+'/temp_HOME'+'/'+samplenames[k]+'_rep'+str(ii+1)))
                  
                  if i[ii].endswith('.gz') and BSSeeker2==True:
                      
                      if classes=="CG":
                      
                          com='zcat'+' '+i[ii]+'''| awk -v OFS='\t' '{if ($2 == "C" && substr($4,1,2)== "CG") {print $1,$3,"+",$4,$7,$8 >> $1".tsv"} else if ($2 == "G" && substr($4,1,2) =="CG")  {print $1,$3,"-",$4,$7,$8 >> $1".tsv"}}'  '''
                      
                      elif classes=="CHG": 
                          
                          com='zcat'+' '+i[ii]+'''| awk -v OFS='\t' '{if ($2 == "C" && substr($4,2,1)!= "G" && substr($4,3,1)== "G") {print $1,$3,"+",$4,$7,$8 >> $1".tsv"} else if ($2 == "G" && substr($4,2,1)!= "G" && substr($4,3,1)== "G")  {print $1,$3,"-",$4,$7,$8 >> $1".tsv"}}'  '''
                      
                      elif classes=="CHH":
                          
                          com='zcat'+' '+i[ii]+ ''' | awk -v OFS='\t' '{if ($2 == "C" && substr($4,2,1)!= "G" && substr($4,3,1)!= "G") {print $1,$3,"+",$4,$7,$8 >> $1".tsv"} else if ($2 == "G" && substr($4,2,1)!= "G" && substr($4,3,1)!= "G")  {print $1,$3,"-",$4,$7,$8 >> $1".tsv"}}'  ''' 
                          
                      elif classes=="CHN": 
                          
                          com='zcat'+' '+i[ii]+ ''' | awk -v OFS='\t' '{if ($2 == "C" && substr($4,2,1)!= "G" ) {print $1,$3,"+",$4,$7,$8 >> $1".tsv"} else if ($2 == "G" && substr($4,2,1)!= "G")  {print $1,$3,"-",$4,$7,$8 >> $1".tsv"}}'  ''' 
                          
                      elif classes=="CNN":
                          
                          com='zcat'+' '+i[ii]+ ''' | awk -v OFS='\t' '{if ($2 == "C" ) {print $1,$3,"+",$4,$7,$8 >> $1".tsv"} else if ($2 == "G" )  {print $1,$3,"-",$4,$7,$8 >> $1".tsv"}}'  ''' 
                      
                  elif  i[ii].endswith('.gz') and BSSeeker2==False: 
                      
                      if classes=="CG":
                      
                          com='zcat'+' '+i[ii]+ ''' | awk -v OFS='\t' '{if (substr($4,1,2)== "CG") {print $0 >> $1".tsv"}}'  '''
                      
                      elif classes=="CHG": 
                          
                          com='zcat'+' '+i[ii]+ ''' | awk -v OFS='\t' '{if (substr($4,2,1)!= "G" && substr($4,3,1)== "G") {print $0 >> $1".tsv"}}'  '''
                      
                      elif classes=="CHH":
                          
                          com='zcat'+' '+i[ii]+ ''' | awk -v OFS='\t' '{if (substr($4,2,1)!= "G" && substr($4,3,1)!= "G") {print $0 >> $1".tsv"}}'  '''
                          
                      elif classes=="CHN": 
                          
                          com='zcat'+' '+i[ii]+ ''' | awk -v OFS='\t' '{if (substr($4,2,1)!= "G" ) {print $0 >> $1".tsv"}}'  '''
                          
                      elif classes=="CNN":
                          
                          com='zcat'+' '+i[ii]+ ''' | awk -v OFS='\t' '{print $0 >> $1".tsv"}'  ''' 
                          
                  elif not i[ii].endswith('.gz') and BSSeeker2==True:
                      
                      if classes=="CG":
                      
                          com= '''  awk -v OFS='\t' '{if ($2 == "C" && substr($4,1,2)== "CG") {print $1,$3,"+",$4,$7,$8 >> $1".tsv"} else if ($2 == "G" && substr($4,1,2) =="CG")  {print $1,$3,"-",$4,$7,$8 >> $1".tsv"}}'  ''' + i[ii]
                      
                      elif classes=="CHG": 
                          
                          com=''' awk -v OFS='\t' '{if ($2 == "C" && substr($4,2,1)!= "G" && substr($4,3,1)== "G") {print $1,$3,"+",$4,$7,$8 >> $1".tsv"} else if ($2 == "G" && substr($4,2,1)!= "G" && substr($4,3,1)== "G")  {print $1,$3,"-",$4,$7,$8 >> $1".tsv"}}'  ''' + i[ii]
                      
                      elif classes=="CHH":
                          
                          com= '''  awk -v OFS='\t' '{if ($2 == "C" && substr($4,2,1)!= "G" && substr($4,3,1)!= "G") {print $1,$3,"+",$4,$7,$8 >> $1".tsv"} else if ($2 == "G" && substr($4,2,1)!= "G" && substr($4,3,1)!= "G")  {print $1,$3,"-",$4,$7,$8 >> $1".tsv"}}'  ''' + i[ii]
                          
                      elif classes=="CHN": 
                          
                          com='''  awk -v OFS='\t' '{if ($2 == "C" && substr($4,2,1)!= "G" ) {print $1,$3,"+",$4,$7,$8 >> $1".tsv"} else if ($2 == "G" && substr($4,2,1)!= "G")  {print $1,$3,"-",$4,$7,$8 >> $1".tsv"}}'  ''' + i[ii]
                          
                      elif classes=="CNN":
                          
                          com='''  awk -v OFS='\t' '{if ($2 == "C" ) {print $1,$3,"+",$4,$7,$8 >> $1".tsv"} else if ($2 == "G" )  {print $1,$3,"-",$4,$7,$8 >> $1".tsv"}}'  ''' + i[ii]
                      
                        
                  else:
                      
                      if classes=="CG":
                      
                          com= '''  awk -v OFS='\t' '{if (substr($4,1,2)== "CG") {print $0 >> $1".tsv"}}'  ''' + i[ii]
                      
                      elif classes=="CHG": 
                          
                          com=''' awk -v OFS='\t' '{if (substr($4,2,1)!= "G" && substr($4,3,1)== "G") {print $0 >> $1".tsv"}}'  ''' + i[ii]
                      
                      elif classes=="CHH":
                          
                          com=''' awk -v OFS='\t' '{if (substr($4,2,1)!= "G" && substr($4,3,1)!= "G") {print $0 >> $1".tsv"}}'  ''' + i[ii]
                          
                      elif classes=="CHN": 
                          
                          com=''' awk -v OFS='\t' '{if (substr($4,2,1)!= "G" ) {print $0 >> $1".tsv"}}'  ''' + i[ii]
                          
                      elif classes=="CNN":
                          
                          com=''' awk -v OFS='\t' '{print $0 >> $1".tsv"}'  ''' + i[ii]
                        
                  status=subprocess.call(com, shell=True)
                  
                  temp_file.append(os.getcwd())
                  os.chdir(cwd)
          input_files_mod.append(temp_file)        
    input_files=input_files_mod
    del(input_files_mod,temp_file)
    s=[ os.path.splitext(os.path.basename(x))[0] for x in glob.glob(input_files[0][0]+'/*.tsv')]
     
    os.chdir(cwd)  
    
      
    if not os.path.exists((o.outputpath+'/temp_HOME'+'/chunks')):
        os.makedirs(o.outputpath+'/temp_HOME'+'/chunks')
    else: 
        print(" Temp directory at output path already exist.... please clean up and rerun")
    if not os.path.exists((o.outputpath+'/HOME_Timeseries_DMRs')):
        os.makedirs(o.outputpath+'/HOME_Timeseries_DMRs') 

     
       
    sc=o.scorecutoff
    d=o.delta
    minlen=o.minlength
    mc=o.minc
    sin=o.singlechrom
    npp=o.numprocess
    if sin==True:
        nop=npp
        npp=1
    else: 
        nop=1
        
   
   #"handle any number of replicates as long as it is 2+ in all groups but cannot handle 1 replicate in 1 group and multiple in the other"
    if (min(numreps)==1 and max(numreps)>1):
        sys.exit('error: cannot handle 1 replicate in 1 group and more than 1 in other')
    
    pd.options.mode.chained_assignment = None
     
    merge = functools.partial(pd.merge, how='inner', on=['chr','pos',"strand","type"])
    dictionary = OrderedDict(zip(list(samplenames),list(input_files)))
    comb_samples=itertools.combinations(list(samplenames), 2)
#    
#          
    if status==0:        
        print"Preparing the DMRs from HOME....." 
        print "GOOD LUCK !" 
        
### multiprocessing the chromosomes        
        
        if npp==1:  
                     
    
                for dx in s:
                   main(dx)
                shutil.rmtree(o.outputpath+'/temp_HOME', ignore_errors=True)
                print "Congratulations the DMRs are ready" 
                remEmptyDir(o.outputpath+'/HOME_DMRs/')
                
          
        elif npp>1:
           
                pool1= multiprocessing.Pool(processes=npp)
                process=[pool1.apply_async(main, args=(dx,)) for dx in s]
                output = [p.get() for p in process]
                pool1.close()
                print "Congratulations the DMRs are ready"
                pool1.join()
                shutil.rmtree(o.outputpath+'/temp_HOME', ignore_errors=True)
                remEmptyDir(o.outputpath+'/HOME_DMRs/')

          