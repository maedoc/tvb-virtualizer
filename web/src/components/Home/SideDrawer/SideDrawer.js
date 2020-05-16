import React from 'react';
import {Link} from 'react-router-dom';

import './SideDrawer.css';
const sideDrawer=props=>{
    let drawerClasses='side_drawer';
    if(props.show){
        drawerClasses='side_drawer open';
    }
    return(<nav className={drawerClasses}>
        <ul>
         <li><Link to="/">Home</Link></li>
         <li><Link to="/input">Input</Link></li>
         <li><Link to="/workflowList">Workflow List</Link></li>
         <li><Link to="/newWorkflow">New Workflow</Link></li>


        </ul>
    </nav>);
};


export default sideDrawer;