import React, { Component } from 'react';
import Header from '../Home/Header/Header';
import Configuration1 from './Configuration1';
import Configuration2 from './Configuration2';
import Configuration3 from './Configuration3';
import Configuration4 from './Configuration4';
import Slider from "react-slick";
import "slick-carousel/slick/slick.css"; 
import "slick-carousel/slick/slick-theme.css";
import './Configuration.css'
class Configuration extends Component{

    render(){
        const settings = {
            dots: true,
            infinite: true,
            speed: 1500,
            slidesToShow: 1,
            slidesToScroll: 1
          };
        return(
            <div>
                <Header/>
                <Slider {...settings}>
                <Configuration1/>
                <Configuration2/>
                <Configuration3/>
                <Configuration4/>
                </Slider>
                <button type="submit" className="proceed_btn" onClick={this.handleClick}>Click Here To Proceed >>></button>


            </div>
            
        )
    }
}
export default Configuration;