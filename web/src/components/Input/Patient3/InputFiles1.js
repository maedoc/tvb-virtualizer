import React, { Component } from 'react';
import axios from 'axios';
import './InputFiles.css'

class InputFiles1 extends Component {
  constructor(props) {
    super(props);
      this.state = {
        selectedFile: null,
        disabled:true

      }
   
  }
  onChangeHandler=event=>{
    this.setState({
      selectedFile: event.target.files[0],
      disabled:false
    })
  }
onClickHandler = event => {
    event.preventDefault();
    const data = new FormData()
    data.append('file', this.state.selectedFile)
    axios.post("http://localhost:8000/upload3", data, { 
       
   })
 .then(res => { 
     console.log(res.statusText)
  })
 }
 

  render() {
    return (
      <div className="container">
               <form className="form">
                   <h1>Upload data for Patient3</h1>
                   <h3> Input T1 data</h3>
                <label className="input_type">T1.nii.gz</label>
                <input type="file" className="input" accept=".nii.gz" onChange={this.onChangeHandler} required/>
             
              
              <button type="button" disabled={this.state.disabled} className="btn" onClick={this.onClickHandler}>Upload</button>
              </form> 
	      </div>
      
    
    );
  }
}

export default InputFiles1;