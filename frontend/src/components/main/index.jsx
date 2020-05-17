import React from 'react';
import { connect } from 'react-redux';
import { TAB_REQUESTS } from '../../constants';
import Header from '../header';
import Requests from '../requests';
import Lists from '../lists';
import { getTab } from '../../redux/selectors';
import './styles/index.scss';


class Main extends React.Component {
    render() {

        const contents = this.props.tab === TAB_REQUESTS
            ? <Requests />
            : <Lists />;

        return (
            <main className="main">
                <Header />
                <div className="contents">
                    { contents }
                </div>
            </main>
        );
    }
}

const mapStateToProps = state => {
    const tab = getTab(state);
    return { tab };
}

export default connect(
    mapStateToProps
    // TODO actions
)(Main);
