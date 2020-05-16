import React from 'react';
import './Toolbar.css';
import logo from '../image/logo.jpg';
import {Link} from 'react-router-dom';
import DrawerToggleButton from '../SideDrawer/DrawerToggleButton';
const toolbar=props=>(
    <header className="toolbar">
        <nav className="toolbar_nav">
            <div>
                <DrawerToggleButton click={props.drawerClickHandler}/>
                </div>
            <div className="toolbar_logo">
                <Link to="/"><img src={logo} alt="demo"/></Link>
                </div>
            <div className="space"/>
            <div className="toolbar_nav_items">
                <ul>
                    <li><Link to="/">Home</Link></li>
                    <li><Link to="/input">Input</Link></li>
                    <li><Link to="/workflowList">Workflow List</Link></li>
                    <li><Link to="/newWorkflow">New Workflow</Link></li>

                </ul>
            </div>
        </nav>
    </header>
);
export default toolbar;