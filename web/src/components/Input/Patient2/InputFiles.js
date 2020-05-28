import React, { Component } from 'react';
import InputFiles1 from './InputFiles1';
import InputFiles2 from './InputFiles2';
import InputFiles3 from './InputFiles3';
import InputFiles4 from './InputFiles4';

import './InputFiles.css'
class InputFiles extends Component {
  render() {
    return (
      <div className="App">
      
        <InputFiles1 />
        <InputFiles2 />
        <InputFiles3/>
        <InputFiles4/>
       </div>
    );
  }
}
export default InputFiles;