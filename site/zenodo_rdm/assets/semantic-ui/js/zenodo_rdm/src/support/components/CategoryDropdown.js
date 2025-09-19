import React, { Component } from "react";
import { PropTypes } from "prop-types";
import { SelectField } from "react-invenio-forms";

class CategoryDropdown extends Component {
  constructor(props) {
    super(props);

    const { categories, defaultCategory, onCategoryChange } = props;
    const activeCategory = categories?.find((el) => el.key === defaultCategory);
    onCategoryChange(activeCategory);
  }

  serializeCategory(category) {
    if (!category) {
      return null;
    }
    return {
      text: category.title,
      value: category.key,
    };
  }

  onChange = ({ data, formikProps }) => {
    const { categories, onCategoryChange } = this.props;
    const activeCategory = categories.find((el) => el.key === data.value);

    onCategoryChange(activeCategory);
    formikProps.form.setFieldValue("category", data.value);
  };

  render() {
    const { categories, activeCategory, className } = this.props;

    const serializedCategories = categories.map((cat) => this.serializeCategory(cat));

    return (
      <>
        <SelectField
          options={serializedCategories}
          fieldPath="category"
          label="Category"
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
    );
  }
}

CategoryDropdown.propTypes = {
  categories: PropTypes.array,
  defaultCategory: PropTypes.string,
  activeCategory: PropTypes.string,
  onCategoryChange: PropTypes.func,
  className: PropTypes.string,
};

CategoryDropdown.defaultProps = {
  categories: [],
  defaultCategory: "",
  activeCategory: "",
  onCategoryChange: null,
  className: "",
};

export default CategoryDropdown;
