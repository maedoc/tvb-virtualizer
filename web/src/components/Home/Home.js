import React, { Component } from 'react';
import Header from './Header/Header';
import Content from './Content/Content';
import './Home.css'
class Home extends Component{
  render(){
    return(
      <div>
        <Header className="head"/> 
        <Content/> 
      </div>
    )
  }
}
export default Home;