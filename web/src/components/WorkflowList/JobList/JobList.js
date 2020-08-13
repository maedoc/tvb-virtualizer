import React, { Component } from 'react';
import axios from 'axios';
import {BootstrapTable,TableHeaderColumn } from 'react-bootstrap-table';
import BeatLoader from "react-spinners/BeatLoader";
import './JobList.css';

class JobList extends Component {
  state = {
    jobs: [],
    success:[],
    failed:[],
    running:[],
    failing:[],
    loading:false,
    noData:''
  }
  componentDidMount() {
    // console.log(this.props.location.sampleParam)
    axios.all([
      axios.get('http://localhost:8000/auth/12'),
      axios.get('http://localhost:8000/auth/12/successful'),
      axios.get('http://localhost:8000/auth/12/failed'),
      axios.get('http://localhost:8000/auth/12/running'),
      axios.get('http://localhost:8000/auth/12/failing')
    ])
      .then(axios.spread((response1, response2, response3, response4, response5) => {  
        // if(!response4.data.length || response5.data.records){
        //   this.setState({noData:true})
        // }
        // else{
          this.setState({
            jobs: response1.data.records,
            success: response2.data.records,
            failed: response3.data.records,
            running: response4.data.records,
            failing: response5.data.records,
            loading:true,
            // noData:false
        });
      // }
    }))
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
       <BootstrapTable data={this.state.success} version="4" striped condensed pagination keyField="job_id">
        <TableHeaderColumn dataField="job_id" >Job ID</TableHeaderColumn>
        <TableHeaderColumn dataField="exec_job_id">Job Name</TableHeaderColumn>
      </BootstrapTable>:
     <div className='spinner'><BeatLoader color={"#00BFFF"}/></div> }
    
     <p className="job">Failed Jobs</p>
     {this.state.loading ? 
       <BootstrapTable data={this.state.failed} version="4" striped condensed pagination keyField="job_id">
        <TableHeaderColumn dataField="job_id" >Job ID</TableHeaderColumn>
        <TableHeaderColumn dataField="exec_job_id">Job Name</TableHeaderColumn>
      </BootstrapTable>:
     <div className='spinner'><BeatLoader color={"#00BFFF"}/></div> }

     <p className="job">Running Jobs</p>
     {this.state.loading ? 
       <BootstrapTable data={this.state.running} version="4" striped condensed pagination keyField="job_id">
        <TableHeaderColumn dataField="job_id" >Job ID</TableHeaderColumn>
        <TableHeaderColumn dataField="exec_job_id">Job Name</TableHeaderColumn>
      </BootstrapTable>:
     <div className='spinner'><BeatLoader color={"#00BFFF"}/></div> }

     <p className="job">Failing Jobs</p>
     {this.state.loading ? 
       <BootstrapTable data={this.state.failing} version="4" striped condensed pagination keyField="job_id">
        <TableHeaderColumn dataField="job_id" >Job ID</TableHeaderColumn>
        <TableHeaderColumn dataField="exec_job_id">Job Name</TableHeaderColumn>
      </BootstrapTable>:
     <div className='spinner'><BeatLoader color={"#00BFFF"}/></div> }
      </div>
    );
  }
}
export default JobList;