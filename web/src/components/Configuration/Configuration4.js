import React, { Component } from 'react';
import './Configuration.css'
class Configuration4 extends Component{
    constructor(props){
        super(props);
        const label1= "openmp.threads"
        const label2= "mrtrix.threads"
        const label3="ct.elec.intensity.th"
        const label4="decim.factor"
        this.state = {  
            "subject":"TVB1",
             "t1.format":"nii",
            "t2.flag":"False",
            "t2.format":"nii",
            "flair.flag":"False",
            "flair.format":"nii",
            "openmp.threads": 4,
            "parcelation.atlas":"default",
            "dwi.scan.direction":"ap",
            "dwi.format":"mif",
            "dwi.use.gradient":"True",
            "dwi.multi.shell":"False",
            "mrtrix.threads": 2,
            "dwi.is.reversed":"False",
            aseg_lh_labels : "8 10 11 12 13 16 17 18 26",
            aseg_rh_labels:"47 49 50 51 52 53 54 58",
            use_flirt:"True",
            strmlns_no:"2M",
            strmlns_sift_no:"1M",
            strmlns_len:250,
            strmlns_step:0.5,
            "ct.flag":"False",
            "ct.format":"nii",
            "bem.surfaces":"False",
            "use.openmeeg":"False",
            "ct.elec.intensity.th":1000,
            "seeg.flag":"False",
            "seeg.gain.use.dp":"False",
            "seeg.gain.use.mrs":"False",
            "eeg.flag":"False",
            "meg.flag":"False",
            "resample.flag":"False",
            "trgsubject":"fsaverage5",
            "decim.factor":0.1,
            os:"LINUX"
        }
    }
    handleChangeAll = (event) =>{
        this.setState ( { [event.target.name] :event.target.value  } )
       }
     
       
    render(){
        const downloadableData = encodeURIComponent(JSON.stringify(this.state,null,2))

        return(
            
            <div className="container">
            <form onSubmit = {this.handlesubmit} className="config_form">

                 <h1>Configuration for Patient 4 </h1>
                   
       
     <label className="l_name"> openmp.threads 
    <input  type="number" name="openmp.threads"  className="field" value={this.state.label1} onChange={this.handleChangeAll} />
        <i  class="fa fa-info-circle fa-1x" title="Default values is 4.Determine no of threads in multi-processing." ></i>
</label>

    <label className="l_name"> mrtrix.threads
    <input  type="number" name="mrtrix.threads" className="field"value= {this.state.label2} onChange={this.handleChangeAll} /> 
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
    <input  type="number" name="ct.elec.intensity.th" className="field" value= {this.state.label3} onChange={this.handleChangeAll} /> 
        <i  class="fa fa-info-circle fa-1x" ></i>
</label>

    <label className="l_name"> decim.factor 
    <input  type="text" name="decim.factor" className="field" value= {this.state.label4} onChange={this.handleChangeAll} /> 
        <i  class="fa fa-info-circle fa-1x" ></i>
</label>

<a href={`data:applicatiom/json,${downloadableData}`} download="patient_flow.properties">Save Data for Patient 4</a>

   </form>
            </div>
            
        )
    }
}
export default Configuration4;