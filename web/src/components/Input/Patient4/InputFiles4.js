import React, { Component } from 'react';
import axios from 'axios';
import './InputFiles.css'

class InputFiles4 extends Component {
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
    axios.post("http://localhost:8000/upload4", data, { 
   })
 .then(res => { 
     console.log(res.statusText)
  })
 }

  render() {
    return (
      <div class="container">
               <form className="form">
                   
                <label className="input_type">DWI.bval</label>
                <input type="file" className="input"  accept=".bval" onChange={this.onChangeHandler} required/>
             
              
              <button type="button" disabled={this.state.disabled} className="btn" onClick={this.onClickHandler}>Upload</button>
              </form>  
	      </div>
      
    
    );
  }
}

export default InputFiles4;