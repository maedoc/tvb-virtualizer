import React, { Component } from 'react';
import axios from 'axios';
import './Configuration.css'
class Configuration4 extends Component{
    constructor(props){
        super(props);
        this.state = {  
           "openmp.threads": 4,
            "mrtrix.threads": 2,
            aseg_lh_labels : "8 10 11 12 13 16 17 18 26",
            aseg_rh_labels:"47 49 50 51 52 53 54 58",
            use_flirt:"True",
            strmlns_no:"2M",
            strmlns_sift_no:"1M",
            strmlns_len:250,
            strmlns_step:0.5,
            "ct.elec.intensity.th":1000,
            "decim.factor":0.1
        }
    }
    handleChangeAll = (event) =>{
        this.setState ( { [event.target.name] :event.target.value  } )
       }
       
    onClickHandler=(event)=>{
 event.preventDefault();
 const label1=this.state["openmp.threads"]
 const label2=this.state["mrtrix.threads"]
 const label3=this.state["ct.elec.intensity.th"]
 const label4=this.state["decim.factor"]
 const aseg_lh_labels=this.state.aseg_lh_labels
 const aseg_rh_labels=this.state.aseg_rh_labels
 const use_flirt=this.state.use_flirt
 const strmlns_no=this.state.strmlns_no
 const strmlns_sift_no=this.state.strmlns_sift_no
 const strmlns_len=this.state.strmlns_len
 const strmlns_step=this.state.strmlns_step
 const data={label1,label2,label3,label4,aseg_lh_labels,aseg_rh_labels,use_flirt,strmlns_no,strmlns_sift_no,strmlns_len,strmlns_step}
 axios.post("http://localhost:8000/input4", data)
.then(res => {
  console.log(res.statusText)
})
    }
    render(){
        return(
            <div className="container">
            
                <form className="config_form">
                 <h1>Configuration for Patient 4 </h1>
                
                   
       
     <label className="l_name"> openmp.threads 
    <input  type="number" name="openmp.threads"  className="field" value={this.state["openmp.threads"]} onChange={this.handleChangeAll} />
    <i  class="fa fa-info-circle fa-1x" title="Default values is 4.Determine no of threads in multi-processing." ></i>
 
    </label>

    <label className="l_name"> mrtrix.threads
    <input  type="number" name="mrtrix.threads" className="field"value= {this.state["mrtrix.threads"]} onChange={this.handleChangeAll} /> 
    <i  class="fa fa-info-circle fa-1x" title="Default value is 2.Set the number of CPU threads to use for multi-threading." ></i>
    </label>

    <label className="l_name"> aseg_lh_labels 
    <input  type="text" name="aseg_lh_labels" className="field" value= {this.state.aseg_lh_labels} onChange={this.handleChangeAll} /> 
    <i  class="fa fa-info-circle fa-1x" title=" used for females who have gone through menopause, the normal range is 14.2–52.3 IU/L."></i>
    </label>

    <label className="l_name"> aseg_rh_labels 
    <input  type="text" name="aseg_rh_labels" className="field" value= {this.state.aseg_rh_labels} onChange={this.handleChangeAll} /> 
    <i  class="fa fa-info-circle fa-1x" ></i>
    </label>

    <label className="l_name"> use_flirt 
    <input  type="text" name="use_flirt" className="field" value= {this.state.use_flirt} onChange={this.handleChangeAll} /> 
    <i  class="fa fa-info-circle fa-1x" ></i>
    </label>

    <label className="l_name"> strmlns_no
    <input  type="text" name="strmlns_no" className="field" value= {this.state.strmlns_no} onChange={this.handleChangeAll} /> 
    <i  class="fa fa-info-circle fa-1x" ></i>
    </label>

    <label className="l_name"> strmlns_sift_no 
    <input  type="text" name="strmlns_sift_no" className="field"  value= {this.state.strmlns_sift_no} onChange={this.handleChangeAll} /> 
    <i  class="fa fa-info-circle fa-1x" ></i>
    </label>

    <label className="l_name"> strmlns_len
    <input  type="number" name="strmlns_len" className="field" value= {this.state.strmlns_len} onChange={this.handleChangeAll} /> 
    <i  class="fa fa-info-circle fa-1x" ></i>
    </label>

    <label className="l_name"> strmlns_step
    <input  type="text" name="strmlns_step" className="field" value= {this.state.strmlns_step} onChange={this.handleChangeAll} /> 
    <i  class="fa fa-info-circle fa-1x" ></i>
    </label>

    <label className="l_name"> ct.elec.intensity.th
    <input  type="number" name="ct.elec.intensity.th" className="field" value= {this.state["ct.elec.intensity.th"]} onChange={this.handleChangeAll} /> 
    <i  class="fa fa-info-circle fa-1x" ></i>
    </label>

    <label className="l_name"> decim.factor 
    <input  type="text" name="decim.factor" className="field" value= {this.state["decim.factor"]} onChange={this.handleChangeAll} /> 
    <i  class="fa fa-info-circle fa-1x" ></i>
    </label>
    <button type="button" className="save_btn" onClick={this.onClickHandler}>Save Data for Patient 4</button>
   </form>
            </div>
            
        )
    }
}
export default Configuration4;