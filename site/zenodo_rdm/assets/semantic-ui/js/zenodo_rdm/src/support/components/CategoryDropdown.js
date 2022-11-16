import React, { Component } from "react";
import { PropTypes } from "prop-types";
import { SelectField } from "react-invenio-forms";
import _find from 'lodash';
import _isEmpty from 'lodash';

class CategoryDropdown extends Component {

    constructor(props) {
        super(props);

        const { categories, defaultCategory } = props;
        const activeCategory = categories?.find((el) => (el.key === defaultCategory));

        this.state = {
            activeCategory: activeCategory,
        }
    }

    serializeCategory(category) {
        if (!category) {
            return null;
        }
        return {
            text: category.title,
            value: category.key
        }
    }

    onChange = ({ data, formikProps }) => {
        const { categories } = this.props;
        const activeCategory = categories.find((el) => (el.key === data.value))
        
        this.setState({
            activeCategory: activeCategory
        });
        formikProps.form.setFieldValue('category', data.value);
    }

    render() {
        const { categories, className } = this.props;
        const { activeCategory} = this.state;

        const serializedCategories = categories.map((cat) => (this.serializeCategory(cat)));

        return (
            <>
                <SelectField
                    options={serializedCategories}
                    fieldPath='category'
                    label='Category'
                    required
                    width={4}
                    onChange={this.onChange}
                    className={className}
                />
                <div
                    className="label-padding"
                    dangerouslySetInnerHTML={{ __html: activeCategory?.description }}
                />
            </>
        )
    }
}

CategoryDropdown.propTypes = {
    categories: PropTypes.array,
    defaultCategory: PropTypes.string,
    className: PropTypes.string,
};

CategoryDropdown.defaultProps = {
    categories: [],
    defaultCategory: '',
    className: '',
};

export default CategoryDropdown;