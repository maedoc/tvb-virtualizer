import React, { Component } from 'react';
import Patient1 from './Patient1/InputFiles';
import Patient2 from './Patient2/InputFiles';
import Patient3 from './Patient3/InputFiles';
import Patient4 from './Patient4/InputFiles';
import Header from '../Home/Header/Header'
import Slider from "react-slick";
import {withRouter} from 'react-router';
import "slick-carousel/slick/slick.css"; 
import "slick-carousel/slick/slick-theme.css";

class Patient extends Component{
    handleClick() {
        alert("Proceed only if all the files are uploaded");
        this.props.history.push('/');
    }
    constructor(props) {
      super(props);
      this.state={
         
      }
      this.handleClick = this.handleClick.bind(this);
    }
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
                <Patient1/>
                <Patient2/>
                <Patient3/>
                <Patient4/>
                </Slider>
                <button type="submit" className="button" onClick={this.handleClick}>Click Here To Proceed >>></button>
            </div>
        )
    }
}
export default withRouter(Patient);