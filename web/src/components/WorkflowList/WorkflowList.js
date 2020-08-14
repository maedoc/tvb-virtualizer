import React, { Component } from 'react';
import axios from 'axios';
import {BootstrapTable,TableHeaderColumn } from 'react-bootstrap-table';
import BeatLoader from "react-spinners/BeatLoader";
import {Link} from 'react-router-dom';
import "./WorkflowList.css"

function showState(cell) {
  return cell.state;
}

function showJobs(cell,row){
  return <Link to={{ pathname: "/jobList/"+row.wf_id }} >{cell}</Link>
}

function rowStyleFormat(row, rowIdx) {
  return { backgroundColor: row.workflow_state.state==='WORKFLOW_TERMINATED'  ? '#F05' : row.workflow_state.state==='WORKFLOW_EXECUTED' ? 'green' :
  row.workflow_state.state==='WORKFLOW_STARTED' ? 'lightblue' : 'gray' };
}
class WorkflowList extends Component {
  state = {
    workflow: [],
    loading:false
  }

  componentDidMount() {
    axios.get('http://localhost:8000/auth')
      .then(response => {
        this.setState({
          workflow: response.data.records,
          loading:true
        });
      });
  }
  
  render() {
    return (
      <div className="workflow_table" >
       <p className="workflow"> Workflow Listing</p>
        {this.state.loading ? 
       <BootstrapTable data={this.state.workflow} version="4" striped condensed pagination search keyField="wf_id" trStyle={rowStyleFormat}>
       <TableHeaderColumn dataField="dax_label" width="200"  dataSort dataFormat={showJobs}>Workflow Lable</TableHeaderColumn>
       <TableHeaderColumn dataField="submit_dir" dataSort >Submit Directory</TableHeaderColumn>
       <TableHeaderColumn dataField="workflow_state" width="200" dataFormat={showState} dataSort >State</TableHeaderColumn>
       <TableHeaderColumn dataField="timestamp" width="250"   dataSort >Submitted On</TableHeaderColumn>
     </BootstrapTable> :
     <div className='spinner'><BeatLoader color={"#00BFFF"}/></div> }

     </div>
    );
  }
}

export default WorkflowList;