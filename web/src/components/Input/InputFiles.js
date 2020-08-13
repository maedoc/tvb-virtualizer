import React, { Component } from 'react';
import axios from 'axios';
import './InputFiles.css'

class InputFiles extends Component {
  constructor(props) {
    super(props);
      this.state = {
        selectedFile1: null,
        selectedFile2: null,   
        selectedFile3: null,   
        selectedFile4: null,
        disabled1:true,
        disabled2:true,
        disabled3:true,
        disabled4:true,

      }
   
  }
  onChangeHandler1=event=>{
    this.setState({
      selectedFile1: event.target.files[0],
      disabled1:false
    })
  }
  onChangeHandler2=event=>{
    this.setState({
      selectedFile2: event.target.files[0],
      disabled2:false
    })
  }
  onChangeHandler3=event=>{
    this.setState({
      selectedFile3: event.target.files[0],
      disabled3:false
    })
  }
  onChangeHandler4=event=>{
    this.setState({
      selectedFile4: event.target.files[0],
      disabled4:false
    })
  }
 
onClickHandler = event => {
  alert("Files Uploaded for Patient "+this.props.no)
    event.preventDefault();
    const data = new FormData()
    data.append('file', this.state.selectedFile1)
    data.append('file', this.state.selectedFile2)
    data.append('file', this.state.selectedFile3)
    data.append('file', this.state.selectedFile4)
    axios.post("http://localhost:8000/upload"+this.props.no, data)
 .then(res => { 
     console.log(res.statusText)
  })
 }
 

  render() {
    return (
      <div className="container">
               <form className="form">
               <h1>Upload data for Patient {this.props.no}</h1>
                   <h3> Input T1 data</h3>
                <label className="file_name">T1.nii.gz
                <input type="file" className="input" accept=".nii.gz" onChange={this.onChangeHandler1}/>
                </label>

                <h3>Input DWI data</h3>
                <label className="file_name">DWI.bvec
                <input type="file" className="input" accept=".bvec" onChange={this.onChangeHandler2}/>
                </label>
                <label className="file_name">DWI.bval
                <input type="file" className="input"  accept=".bval" onChange={this.onChangeHandler3}/>
                </label>
                <label className="file_name">DWI.nii
                <input type="file" className="input" accept=".nii" onChange={this.onChangeHandler4}/>
                </label>
              <button type="button" disabled={this.state.disabled1 || this.state.disabled2 || this.state.disabled3 ||this.state.disabled4} className="btn" onClick={this.onClickHandler}>Upload Input Files for Patient {this.props.no}</button>
              </form> 
	      </div>
      
    
    );
  }
}

export default InputFiles;