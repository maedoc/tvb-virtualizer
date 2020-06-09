import React from 'react';
import './ProcessType.css';
import {withRouter} from 'react-router';

class ProcessType extends React.Component {
    constructor() {
      super();
      
      this.state = {
        type: ''
      };
      
      this.handleChange = this.handleChange.bind(this);
      this.handleClick = this.handleClick.bind(this);
    }
    
    handleChange(event) {
      this.setState({
        type: event.target.value
      });
    }
    
    handleClick(event) {
      event.preventDefault();
      alert(`You chose the ${this.state.type} processing type and Proceed only if all the files are uploaded.`);
      this.props.history.push('/configuration');
    }
    
    render() {
      return (
        <form onSubmit={this.handleClick}>
          <div className="title">
          <label>
              <strong>Select the Data Processing Type :</strong>
              <input
                  type="radio"
                  value="Sequential"
                  checked={this.state.type === "Sequential"}
                  onChange={this.handleChange}
                />
                Sequential
                &nbsp;
                <input
                  type="radio"
                  value="Parallel"
                  checked={this.state.type === "Parallel"}
                  onChange={this.handleChange}
                />
                Parallel
              </label></div>
              
            
              <button type="submit" className="button" onClick={this.handleClick}>Click Here To Proceed >>></button>

  
        </form>
      );
    }
  }
  
  export default withRouter(ProcessType);
