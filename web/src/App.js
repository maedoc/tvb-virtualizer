import React, { Component } from "react";
import { BrowserRouter as Router,Switch,Route } from "react-router-dom";
import Home from "./components/Home/Home";
import Input from './components/Input/Patient';
import WorkflowList from './components/WorkflowList/WorkflowList';
import NewWorkflow from './components/NewWorkflow/NewWorkflow';
class App extends Component {
  render(){
    return (
      <Router>
      <div>
        <Switch>
          <Route path="/workflowList">
            <WorkflowList />
          </Route>
          <Route path="/newWorkflow">
            <NewWorkflow />
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