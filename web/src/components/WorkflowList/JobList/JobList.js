import React, { Component } from 'react';
import axios from 'axios';
import {BootstrapTable,TableHeaderColumn } from 'react-bootstrap-table';
import BeatLoader from "react-spinners/BeatLoader";
import {withRouter} from 'react-router-dom';
import './JobList.css';

function runningStyle(row) {
  return { backgroundColor: row  ='lightblue'  };
}
function failingStyle(row) {
  return { backgroundColor: row  ='gray'  };
}
function failedStyle(row) {
  return { backgroundColor: row  ='#F05'  };
}
function successfulStyle(row) {
  return { backgroundColor: row  ='green'  };
}
class JobList extends Component {
  constructor() {
    super();
  this.state = {
    jobs: [],
    successful:[],
    failed:[],
    running:[],
    failing:[],
    loading:false
  }
  this.handleClick = this.handleClick.bind(this);
}

  handleClick=(event)=>{
    event.preventDefault();
    this.props.history.push('/daxgraph');
  }

  componentDidMount() {
    var wf_id=this.props.match.params.jobid
    axios.get('http://localhost:8000/auth/'+wf_id)
    .then(response => {
      this.setState({
        jobs: response.data.records,
        loading:true
      });
    })
    axios.get('http://localhost:8000/auth/'+wf_id+'/successful')
    .then(response => {
      this.setState({
        successful: response.data.records,
        loading:true
      });
    });
    axios.get('http://localhost:8000/auth/'+wf_id+'/failed')
    .then(response => {
      this.setState({
        failed: response.data.records,
        loading:true
      });
    });
    axios.get('http://localhost:8000/auth/'+wf_id+'/running')
    .then(response => {
      this.setState({
        running: response.data.records,
        loading:true
      });
    });
    axios.get('http://localhost:8000/auth/'+wf_id+'/failing')
    .then(response => {
      this.setState({
        failing: response.data.records,
        loading:true
      });
    });
  }


  render() {
    return (
      <div className="job_table" >
       <p className="job"> Jobs Details</p>
       {this.state.loading ? 
       <BootstrapTable data={this.state.jobs} version="4" striped condensed pagination keyField="job_id">
        <TableHeaderColumn dataField="job_id" >Job ID</TableHeaderColumn>
        <TableHeaderColumn dataField="exec_job_id">Job Name</TableHeaderColumn>
        <TableHeaderColumn dataField="type_desc">Type</TableHeaderColumn>
      </BootstrapTable>:
     <div className='spinner'><BeatLoader color={"#00BFFF"}/></div> }
     
      <p className="job"> Successful Jobs</p>
     {this.state.loading ? 
       <BootstrapTable data={this.state.successful} version="4" striped condensed pagination trStyle={successfulStyle} keyField="job_id">
        <TableHeaderColumn dataField="job_id" >Job ID</TableHeaderColumn>
        <TableHeaderColumn dataField="exec_job_id">Job Name</TableHeaderColumn>
      </BootstrapTable>:
     <div className='spinner'><BeatLoader color={"#00BFFF"}/></div> }
    
     <p className="job">Failed Jobs</p>
     {this.state.loading ? 
       <BootstrapTable data={this.state.failed} version="4" striped condensed pagination trStyle={failedStyle} keyField="job_id">
        <TableHeaderColumn dataField="job_id" >Job ID</TableHeaderColumn>
        <TableHeaderColumn dataField="exec_job_id">Job Name</TableHeaderColumn>
      </BootstrapTable>:
     <div className='spinner'><BeatLoader color={"#00BFFF"}/></div> }

     <p className="job">Running Jobs</p>
     {this.state.loading ? 
       <BootstrapTable data={this.state.running} version="4" striped condensed pagination trStyle={runningStyle} keyField="job_id">
        <TableHeaderColumn dataField="job_id" >Job ID</TableHeaderColumn>
        <TableHeaderColumn dataField="exec_job_id">Job Name</TableHeaderColumn>
      </BootstrapTable>:
     <div className='spinner'><BeatLoader color={"#00BFFF"}/></div> }

     <p className="job">Failing Jobs</p>
     {this.state.loading ? 
       <BootstrapTable data={this.state.failing} version="4" striped condensed pagination trStyle={failingStyle} keyField="job_id">
        <TableHeaderColumn dataField="job_id" >Job ID</TableHeaderColumn>
        <TableHeaderColumn dataField="exec_job_id">Job Name</TableHeaderColumn>
      </BootstrapTable>:
     <div className='spinner'><BeatLoader color={"#00BFFF"}/></div> }


    <button className="button_dax" onClick={this.handleClick}>Click Here To View the DAX </button>
    </div>
    );
  }
}
export default withRouter(JobList);
