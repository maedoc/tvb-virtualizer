import React, { Component } from "react";
import { BrowserRouter as Router,Switch,Route } from "react-router-dom";
import Home from "./components/Home/Home";
import Input from './components/Input/Input';
import Configuration from './components/Configuration/Configuration'
import WorkflowList from './components/WorkflowList/WorkflowList';
import JobList from './components/WorkflowList/JobList/JobList';
import DAXGraph from './components/WorkflowList/JobList/DAXGraph'

class App extends Component {
  render(){
    return (
      <Router>
      <div>
        <Switch>
          <Route path="/jobList/:jobid">
            <JobList />
          </Route>
          <Route path="/daxgraph">
            <DAXGraph />
          </Route>
          <Route path="/workflowList">
            <WorkflowList />
          </Route>
          <Route path="/configuration">
            <Configuration />
          </Route>
          <Route path="/input">
            <Input />
          </Route>
          <Route path="/">
            <Home />
          </Route>
        </Switch>
      </div>
      </Router>
          );
  }
  
}
export default App;