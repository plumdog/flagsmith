import ModalHR from 'components/modals/ModalHR'
import { oneOf } from 'prop-types'
/**
 * Created by kylejohnson on 30/07/2016.
 */
const Tabs = class extends React.Component {
  static displayName = 'Tabs'
  constructor() {
    super()
    this.state = {
      value: 0,
    }
  }
  render() {
    const children = this.props.children.filter((c) => !!c)
    const value = this.props.uncontrolled ? this.state.value : this.props.value
    return (
      <div className={`tabs ${this.props.className || ''}`}>
        <div
          className={`tabs-nav mx-3 ${this.props.theme}`}
          style={isMobile ? { flexWrap: 'wrap' } : {}}
        >
          {children.map((child, i) => {
            const isSelected = value == i
            if (!child) {
              return null
            }
            return (
              <Button
                type='button'
                data-test={child.props['data-test']}
                id={child.props.id}
                key={`button${i}`}
                onClick={(e) => {
                  e.stopPropagation()
                  e.preventDefault()
                  if (this.props.uncontrolled) {
                    this.setState({ value: i })
                  } else {
                    this.props.onChange(i)
                  }
                }}
                className={`btn-tab ${isSelected ? ' tab-active' : ''}`}
              >
                {child.props.tabLabel}
              </Button>
            )
          })}
          {this.props.theme === 'tab' && (
            <div
              className='tab-line'
              style={{
                left: `${(100 / children.length) * value}%`,
                width: `${100 / children.length}%`,
              }}
            />
          )}
        </div>
        {this.props.theme === 'tab' && <ModalHR className='mx-3' />}
        <div className='tabs-content'>
          {children.map((child, i) => {
            const isSelected = value === i
            return (
              <div
                key={`content${i}`}
                className={`tab-item px-3${isSelected ? ' tab-active' : ''}`}
              >
                {child}
              </div>
            )
          })}
        </div>
      </div>
    )
  }
}

Tabs.defaultProps = {
  className: '',
  theme: 'tab',
  value: 0,
}

Tabs.propTypes = {
  children: RequiredElement,
  onChange: OptionalFunc,
  theme: oneOf(['tab', 'pill']),
  uncontrolled: OptionalBool,
  value: OptionalNumber,
}

export default Tabs

// Example Usage
//   <Tabs value={this.state.tab} onChange={this.selectTab}>
//     <TabItem tabLabel={(<span className="fa fa-phone tab-icon"/>)}>
//       <h2>Tab 1 content</h2>
//     </TabItem>
//     <TabItem tabLabel={(<span className="fa fa-phone tab-icon"/>)}>
//       <h2>Tab 2 content</h2>
//     </TabItem>
//   </Tabs>
