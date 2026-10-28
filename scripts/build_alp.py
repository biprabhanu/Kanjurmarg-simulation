"""
Generates the native AnyLogic 8.8 project file (version 2, final assumptions)
    anylogic/Kanjurmarg_FOB_Simulation/Kanjurmarg_FOB_Simulation.alp

The XML element structure follows real AnyLogic 8.8.3 project files (AlpVersion 8.8.3).
engine/FobEngine.java is embedded verbatim as Main's "Additional class code", so the model
runs exactly the same stochastic logic that produced the CSV results.

    python3 scripts/build_alp.py
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_NAME = "Kanjurmarg_FOB_Simulation"
PKG = "kanjurmarg_fob_simulation"
OUT_DIR = os.path.join(ROOT, "anylogic", MODEL_NAME)

_next_id = [1761600000000]


def nid():
    _next_id[0] += 1
    return _next_id[0]


def cdata(s):
    return "<![CDATA[" + s.replace("]]>", "]]]]><![CDATA[>") + "]]>"


def argb(hex_rgb, alpha=255):
    """'#RRGGBB' -> AnyLogic signed 32-bit ARGB integer."""
    h = hex_rgb.lstrip("#")
    v = (alpha << 24) | int(h, 16)
    return v - (1 << 32) if v >= (1 << 31) else v


# ------------------------------------------------------------------ palette
C = dict(
    bg="#F4F6F9", ink="#1F2933", muted="#5F6B7A", faint="#9AA5B1", card="#FFFFFF", cardline="#DCE1E8",
    ground="#E7EDE3", road="#C9D0D8", roadline="#FFFFFF", paving="#ECE7DE", tree="#7BA889", tree_dark="#5E8C6C",
    platform="#D9DDE3", platform_edge="#B4BDC8", canopy="#C3CBD5", safety="#E9B824",
    ballast="#D3CEC5", sleeper="#B3A99B", rail="#5B6573",
    train_body="#F3EFE6", train_stripe="#9C2F3A", train_window="#3E4C5E", train_roof="#D9D3C7",
    teal="#00A19B", teal_soft="#CDEDEC", blue="#2563EB", blue_soft="#DCE7FD",
    red="#D93025", red_soft="#FBE2E0", amber="#D97706", purple="#7C3AED", purple_soft="#EDE7F6",
)

PX_PER_M = 8.0
OX, OY = 40, 150     # pixel origin of the station layout (metres -> pixels)


def X(m):
    return OX + m * PX_PER_M


def Y(m):
    return OY + m * PX_PER_M


def M(m):
    return m * PX_PER_M


# ------------------------------------------------------------------ shape helpers
def common(name, x, y, public=True):
    return (f"<Id>{nid()}</Id><Name>{cdata(name)}</Name><X>{x:g}</X><Y>{y:g}</Y>"
            f"<Label><X>10</X><Y>0</Y></Label><PublicFlag>{'true' if public else 'false'}</PublicFlag>"
            f"<PresentationFlag>true</PresentationFlag><ShowLabel>false</ShowLabel>")


_shape_n = [0]


def sname(prefix):
    _shape_n[0] += 1
    return f"{prefix}{_shape_n[0]}"


def _fill(fill):
    return "<FillColor/>" if fill is None else f"<FillColor>{argb(fill)}</FillColor>"


def _line(line):
    return "<LineColor/>" if line is None else f"<LineColor>{argb(line)}</LineColor>"


def rect(x, y, w, h, fill=None, line=None, lw=1, name=None, style="SOLID"):
    name = name or sname("rect_")
    return (f"<Rectangle>{common(name, x, y)}<DrawMode>SHAPE_DRAW_2D</DrawMode><EmbeddedIcon>false</EmbeddedIcon>"
            f"<Z>0</Z><ZHeight>10</ZHeight><LineWidth>{lw:g}</LineWidth>{_line(line)}"
            f"<LineMaterial>null</LineMaterial><LineStyle>{style}</LineStyle><Width>{w:g}</Width><Height>{h:g}</Height>"
            f"<Rotation>0.0</Rotation>{_fill(fill)}<FillMaterial>null</FillMaterial></Rectangle>")


def rrect(x, y, w, h, radius, fill=None, line=None, lw=1, name=None):
    name = name or sname("rrect_")
    return (f"<RoundedRectangle>{common(name, x, y)}<DrawMode>SHAPE_DRAW_2D</DrawMode><EmbeddedIcon>false</EmbeddedIcon>"
            f"<Z>0</Z><ZHeight>10</ZHeight><LineWidth>{lw:g}</LineWidth>{_line(line)}"
            f"<LineMaterial>null</LineMaterial><LineStyle>SOLID</LineStyle><Width>{w:g}</Width><Height>{h:g}</Height>"
            f"<Rotation>0.0</Rotation>{_fill(fill)}<FillMaterial>null</FillMaterial><ArcRadius>{radius:g}</ArcRadius>"
            f"</RoundedRectangle>")


def poly(points, line, lw=1, closed=False, fill=None, name=None, style="SOLID"):
    name = name or sname("line_")
    x0, y0 = points[0]
    pts = "".join(f"<Point><X>{px - x0:g}</X><Y>{py - y0:g}</Y><Z>0</Z></Point>" for px, py in points)
    return (f"<Polyline>{common(name, x0, y0)}<DrawMode>SHAPE_DRAW_2D</DrawMode><EmbeddedIcon>false</EmbeddedIcon>"
            f"<Z>0</Z><ZHeight>10</ZHeight><LineWidth>{lw:g}</LineWidth><LineColor>{argb(line)}</LineColor>"
            f"<LineMaterial>null</LineMaterial><LineStyle>{style}</LineStyle><BeginArrowSize>1</BeginArrowSize>"
            f"<BeginArrowStyle>0</BeginArrowStyle><EndArrowSize>1</EndArrowSize><EndArrowStyle>0</EndArrowStyle>"
            f"{_fill(fill)}<FillMaterial>null</FillMaterial>"
            f"<Points>{pts}</Points><Closed>{'true' if closed else 'false'}</Closed></Polyline>")


def text(x, y, s, size=12, color="ink", bold=False, align="LEFT", code=None, name=None, font="SansSerif"):
    name = name or sname("text_")
    return (f"<Text>{common(name, x, y)}<DrawMode>SHAPE_DRAW_2D</DrawMode><EmbeddedIcon>false</EmbeddedIcon><Z>0</Z>"
            f"<Rotation>0.0</Rotation><Color>{argb(C.get(color, color))}</Color><Text>{cdata(s)}</Text>"
            f"{'' if code is None else f'<TextCode>{cdata(code)}</TextCode>'}"
            f"<Font><Name>{font}</Name><Size>{size}</Size><Style>{1 if bold else 0}</Style></Font>"
            f"<Alignment>{align}</Alignment></Text>")


def oval(x, y, r, fill, fill_code=None, name=None, line=None, lw=1):
    name = name or sname("oval_")
    return (f"<Oval>{common(name, x, y)}<DrawMode>SHAPE_DRAW_2D</DrawMode><EmbeddedIcon>false</EmbeddedIcon><Z>0</Z>"
            f"<ZHeight>10</ZHeight><LineWidth>{lw:g}</LineWidth>{_line(line)}"
            f"<LineMaterial>null</LineMaterial><LineStyle>SOLID</LineStyle><RadiusX>{r:g}</RadiusX><RadiusY>{r:g}</RadiusY>"
            f"<Rotation>0.0</Rotation><FillColor>{argb(fill)}</FillColor>"
            f"{'' if fill_code is None else f'<FillColorCode>{cdata(fill_code)}</FillColorCode>'}"
            f"<FillMaterial>null</FillMaterial></Oval>")


def button(x, y, w, h, label, action, name):
    return (f"<Control Type=\"Button\"><EmbeddedIcon>false</EmbeddedIcon>{common(name, x, y)}"
            f"<DrawMode>SHAPE_DRAW_2D3D</DrawMode><BasicProperties Width=\"{w}\" Height=\"{h}\">"
            f"<EmbeddedIcon>false</EmbeddedIcon><TextColor/><Enabled>true</Enabled><ActionCode>{cdata(action)}</ActionCode>"
            f"</BasicProperties><ExtendedProperties><Font Name=\"Dialog\" Size=\"12\" Style=\"1\"/>"
            f"<LabelText>{cdata(label)}</LabelText></ExtendedProperties></Control>")


def card(x, y, w, h, accent=None):
    out = rrect(x, y, w, h, 8, fill=C["card"], line=C["cardline"], lw=1)
    if accent:
        out += rect(x, y + 10, 4, h - 20, fill=accent, line=None, lw=0)
    return out


# ------------------------------------------------------------------ model-level helpers
def time_unit(code, unit="SECOND"):
    return f"<Code>{cdata(code)}</Code><Unit Class=\"TimeUnits\">{cdata(unit)}</Unit>"


def agent_header(class_id, name, gen_id, extra=""):
    return f"""
		<ActiveObjectClass>
			<Id>{class_id}</Id>
			<Name>{cdata(name)}</Name>
			{extra}
			<Generic>false</Generic>
			<GenericParameter>
				<Id>{gen_id}</Id>
				<Name>{cdata(str(gen_id))}</Name>
				<GenericParameterValue Class="CodeValue">
					<Code>{cdata('T extends Agent')}</Code>
				</GenericParameterValue>
				<GenericParameterLabel>{cdata('Generic parameter:')}</GenericParameterLabel>
			</GenericParameter>
			<FlowChartsUsage>ENTITY</FlowChartsUsage>
			<SamplesToKeep>100</SamplesToKeep>
			<LimitNumberOfArrayElements>false</LimitNumberOfArrayElements>
			<ElementsLimitValue>100</ElementsLimitValue>
			<MakeDefaultViewArea>true</MakeDefaultViewArea>
			<SceneGridColor/>
			<SceneBackgroundColor/>
			<SceneSkybox>null</SceneSkybox>"""


def agent_props(speed="1.3"):
    return f"""
			<AgentProperties>
				<EnvironmentDefinesInitialLocation>true</EnvironmentDefinesInitialLocation>
				<RotateAnimationTowardsMovement>false</RotateAnimationTowardsMovement>
				<RotateAnimationVertically>false</RotateAnimationVertically>
				<VelocityCode Class="CodeUnitValue">
					<Code>{cdata(speed)}</Code>
					<Unit Class="SpeedUnits">{cdata('MPS')}</Unit>
				</VelocityCode>
				<PhysicalLength Class="CodeUnitValue">
					<Code>{cdata('0.5')}</Code>
					<Unit Class="LengthUnits">{cdata('METER')}</Unit>
				</PhysicalLength>
				<PhysicalWidth Class="CodeUnitValue">
					<Code>{cdata('0.5')}</Code>
					<Unit Class="LengthUnits">{cdata('METER')}</Unit>
				</PhysicalWidth>
				<PhysicalHeight Class="CodeUnitValue">
					<Code>{cdata('1.7')}</Code>
					<Unit Class="LengthUnits">{cdata('METER')}</Unit>
				</PhysicalHeight>
			</AgentProperties>"""


def env_props(width, height, layout="USER_DEF"):
    return f"""
			<EnvironmentProperties>
					<EnableSteps>false</EnableSteps>
					<StepDurationCode Class="CodeUnitValue">
						{time_unit('1.0')}
					</StepDurationCode>
					<SpaceType>CONTINUOUS</SpaceType>
					<WidthCode>{cdata(str(width))}</WidthCode>
					<HeightCode>{cdata(str(height))}</HeightCode>
					<ZHeightCode>{cdata('0')}</ZHeightCode>
					<ColumnsCountCode>{cdata('100')}</ColumnsCountCode>
					<RowsCountCode>{cdata('100')}</RowsCountCode>
					<NeigborhoodType>MOORE</NeigborhoodType>
					<LayoutType>{layout}</LayoutType>
					<LayoutTypeApplyOnStartup>true</LayoutTypeApplyOnStartup>
					<NetworkType>USER_DEF</NetworkType>
					<NetworkTypeApplyOnStartup>true</NetworkTypeApplyOnStartup>
					<ConnectionsPerAgentCode>{cdata('2')}</ConnectionsPerAgentCode>
					<ConnectionsRangeCode>{cdata('50')}</ConnectionsRangeCode>
					<NeighborLinkFractionCode>{cdata('0.95')}</NeighborLinkFractionCode>
					<MCode>{cdata('10')}</MCode>
			</EnvironmentProperties>
			<DatasetsCreationProperties>
				<AutoCreate>false</AutoCreate>
					<OccurrenceAtTime>true</OccurrenceAtTime>
					<OccurrenceDate>1761535800000</OccurrenceDate>
					<OccurrenceTime Class="CodeUnitValue">
						{time_unit('0')}
					</OccurrenceTime>
					<RecurrenceCode Class="CodeUnitValue">
						{time_unit('1')}
					</RecurrenceCode>
			</DatasetsCreationProperties>"""


def scale_ruler(inherited):
    return f"""
			<ScaleRuler>
				<Id>{nid()}</Id>
				<Name>{cdata('scale')}</Name>
				<X>{OX}</X><Y>{OY - 40}</Y>
				<PublicFlag>false</PublicFlag>
				<PresentationFlag>false</PresentationFlag>
				<ShowLabel>false</ShowLabel>
				<DrawMode>SHAPE_DRAW_2D3D</DrawMode>
				<Length>80</Length>
				<Rotation>0</Rotation>
				<ScaleType>BASED_ON_LENGTH</ScaleType>
				<ModelLength>10</ModelLength>
				<LengthUnits>METER</LengthUnits>
				<Scale>8</Scale>
				<InheritedFromParentAgentType>{'true' if inherited else 'false'}</InheritedFromParentAgentType>
			</ScaleRuler>"""


def parameter(name, typ, default, x, y, label):
    return f"""
				<Variable Class="Parameter">
					<Id>{nid()}</Id>
					<Name>{cdata(name)}</Name>
					<X>{x}</X><Y>{y}</Y>
					<Label><X>10</X><Y>0</Y></Label>
					<PublicFlag>false</PublicFlag>
					<PresentationFlag>true</PresentationFlag>
					<ShowLabel>true</ShowLabel>
					<Properties SaveInSnapshot="true" ModificatorType="STATIC">
						<Type>{cdata(typ)}</Type>
						<UnitType>{cdata('NONE')}</UnitType>
						<SdArray>false</SdArray>
						<DefaultValue Class="CodeValue">
							<Code>{cdata(default)}</Code>
						</DefaultValue>
						<ParameterEditor>
							<Id>{nid()}</Id>
							<Label>{cdata(label)}</Label>
							<EditorContolType>TEXT_BOX</EditorContolType>
							<MinSliderValue>{cdata('0')}</MinSliderValue>
							<MaxSliderValue>{cdata('100')}</MaxSliderValue>
							<DelimeterType>NO_DELIMETER</DelimeterType>
						</ParameterEditor>
					</Properties>
				</Variable>"""


def plain_var(name, typ, init, x, y):
    init_xml = "" if init is None else f"""
						<InitialValue Class="CodeValue">
							<Code>{cdata(init)}</Code>
						</InitialValue>"""
    return f"""
				<Variable Class="PlainVariable">
					<Id>{nid()}</Id>
					<Name>{cdata(name)}</Name>
					<X>{x}</X><Y>{y}</Y>
					<Label><X>10</X><Y>0</Y></Label>
					<PublicFlag>false</PublicFlag>
					<PresentationFlag>true</PresentationFlag>
					<ShowLabel>true</ShowLabel>
					<Properties SaveInSnapshot="true" Constant="false" AccessType="public" StaticVariable="false">
						<Type>{cdata(typ)}</Type>{init_xml}
					</Properties>
				</Variable>"""


def function(name, ret, body, x, y, params=(), returns=False):
    p = "".join(f"<Parameter><Name>{cdata(n)}</Name><Type>{cdata(t)}</Type></Parameter>" for n, t in params)
    return f"""
				<Function AccessType="default" StaticFunction="false">
					<ReturnModificator>{'RETURNS_VALUE' if returns else 'VOID'}</ReturnModificator>
					<ReturnType>{cdata(ret)}</ReturnType>
					<Id>{nid()}</Id>
					<Name>{cdata(name)}</Name>
					<X>{x}</X><Y>{y}</Y>
					<Label><X>10</X><Y>0</Y></Label>
					<PublicFlag>false</PublicFlag>
					<PresentationFlag>true</PresentationFlag>
					<ShowLabel>true</ShowLabel>
					{p}
					<Body>{cdata(body)}</Body>
				</Function>"""


def dynamic_event(name, params, action, x, y):
    p = "".join(f"<Parameter><Name>{cdata(n)}</Name><Type>{cdata(t)}</Type></Parameter>" for n, t in params)
    return f"""
				<DynamicEventClass>
					<Id>{nid()}</Id>
					<Name>{cdata(name)}</Name>
					<X>{x}</X><Y>{y}</Y>
					<Label><X>10</X><Y>0</Y></Label>
					<PublicFlag>false</PublicFlag>
					<PresentationFlag>true</PresentationFlag>
					<ShowLabel>true</ShowLabel>
					{p}
					<Action>{cdata(action)}</Action>
				</DynamicEventClass>"""


def cyclic_event(name, first, period, action, x, y):
    return f"""
				<Event>
					<Id>{nid()}</Id>
					<Name>{cdata(name)}</Name>
					<X>{x}</X><Y>{y}</Y>
					<Label><X>10</X><Y>0</Y></Label>
					<PublicFlag>false</PublicFlag>
					<PresentationFlag>true</PresentationFlag>
					<ShowLabel>true</ShowLabel>
					<Properties TriggerType="timeout" Mode="cyclic">
						<Timeout Class="CodeUnitValue">
							{time_unit(period)}
						</Timeout>
						<Rate Class="CodeUnitValue">
							<Code>{cdata('1')}</Code>
							<Unit Class="RateUnits">{cdata('PER_SECOND')}</Unit>
						</Rate>
						<OccurrenceAtTime>true</OccurrenceAtTime>
						<OccurrenceDate>1761535860000</OccurrenceDate>
						<OccurrenceTime Class="CodeUnitValue">
							{time_unit(first)}
						</OccurrenceTime>
						<RecurrenceCode Class="CodeUnitValue">
							{time_unit(period)}
						</RecurrenceCode>
						<Condition>{cdata('false')}</Condition>
					</Properties>
					<Action>{cdata(action)}</Action>
				</Event>"""


def histogram_data(name, x, y):
    return f"""
				<HistogramData>
					<Id>{nid()}</Id>
					<Name>{cdata(name)}</Name>
					<X>{x}</X><Y>{y}</Y>
					<Label><X>15</X><Y>0</Y></Label>
					<PublicFlag>false</PublicFlag>
					<PresentationFlag>true</PresentationFlag>
					<ShowLabel>true</ShowLabel>
					<AutoUpdate>false</AutoUpdate>
					<OccurrenceAtTime>true</OccurrenceAtTime>
					<OccurrenceDate>1761535800000</OccurrenceDate>
					<OccurrenceTime Class="CodeUnitValue">
						{time_unit('0')}
					</OccurrenceTime>
					<RecurrenceCode Class="CodeUnitValue">
						{time_unit('60')}
					</RecurrenceCode>
					<Value>{cdata('')}</Value>
					<NumberOfIntervals>15</NumberOfIntervals>
					<MinMaxAutodetect>false</MinMaxAutodetect>
					<RangeMinExpression>{cdata('0')}</RangeMinExpression>
					<RangeMaxExpression>{cdata('30')}</RangeMaxExpression>
					<InitialIntervalSize>{cdata('2')}</InitialIntervalSize>
					<CalculateCDF>false</CalculateCDF>
					<CalculatePercentiles>false</CalculatePercentiles>
					<LowPercent>10</LowPercent>
					<HighPercent>10</HighPercent>
					<Title>{cdata(name)}</Title>
				</HistogramData>"""


def chart_frame(w, h, xoff, yoff, cw, ch):
    return f"""<EmbeddedIcon>false</EmbeddedIcon>
					<Width>{w}</Width>
					<Height>{h}</Height>
					<BackgroundColor/>
					<BorderColor/>
					<ChartArea>
						<XOffset>{xoff}</XOffset>
						<YOffset>{yoff}</YOffset>
						<Width>{cw}</Width>
						<Height>{ch}</Height>
						<BackgroundColor>{argb('#FFFFFF')}</BackgroundColor>
						<BorderColor>{argb(C['cardline'])}</BorderColor>
						<GridColor>{argb('#E4E7EB')}</GridColor>
					</ChartArea>
					<Legend>
						<Place>SOUTH</Place>
						<TextColor>{argb(C['muted'])}</TextColor>
						<Size>22</Size>
					</Legend>
					<Labels>
						<HorLabelsPosition>DEFAULT</HorLabelsPosition>
						<VerLabelsPosition>DEFAULT</VerLabelsPosition>
						<TextColor>{argb(C['muted'])}</TextColor>
					</Labels>
					<ShowLegend>true</ShowLegend>"""


def time_plot(name, x, y, w, h, series, vmax):
    ds = ""
    for title, expr, col in series:
        ds += f"""
					<DatasetExpression>
						<Title>{cdata(title)}</Title>
					<Id>{nid()}</Id>
					<Expression>{cdata('ds_' + expr)}</Expression>
					<Color>{argb(col)}</Color>
					<Expression2>{cdata(expr)}</Expression2>
					<Expression2Flag>true</Expression2Flag>
						<PointStyle>NONE</PointStyle>
						<LineWidth>2.0</LineWidth>
					</DatasetExpression>"""
    return f"""
    			<TimePlot>
					<Id>{nid()}</Id>
					<Name>{cdata(name)}</Name>
					<X>{x}</X><Y>{y}</Y>
					<Label><X>0</X><Y>-10</Y></Label>
					<PublicFlag>true</PublicFlag>
					<PresentationFlag>true</PresentationFlag>
					<ShowLabel>false</ShowLabel>
					<DrawMode>SHAPE_DRAW_2D3D</DrawMode>
					<AutoUpdate>true</AutoUpdate>
					<OccurrenceAtTime>true</OccurrenceAtTime>
					<OccurrenceDate>1761535860000</OccurrenceDate>
					<OccurrenceTime Class="CodeUnitValue">
						{time_unit('60.5')}
					</OccurrenceTime>
					<RecurrenceCode Class="CodeUnitValue">
						{time_unit('60')}
					</RecurrenceCode>
					{chart_frame(w, h, 40, 10, w - 60, h - 60)}
					<TimeWindowsMovementType>MOVEMENT_WITH_TIME</TimeWindowsMovementType>
					<TimeWindowUnits>DAY</TimeWindowUnits>
					<VerScaleFromExpression>{cdata('0')}</VerScaleFromExpression>
					<VerScaleToExpression>{cdata(str(vmax))}</VerScaleToExpression>
					<VerScaleType>FIXED</VerScaleType>
					<DrawLine>true</DrawLine>
					<Interpolation>LINEAR</Interpolation>{ds}
					<SamplesToKeep>200</SamplesToKeep>
					<TimeWindowExpression>{cdata('1.0 / 24.0')}</TimeWindowExpression>
					<FillAreaUnderLine>false</FillAreaUnderLine>
					<LabelFormat>MODEL_DATE_TIME_ONLY</LabelFormat>
    			</TimePlot>"""


def histogram_chart(name, x, y, w, h, series):
    ds = ""
    for title, data, col in series:
        ds += f"""
					<HistogramDataExpression>
					<Id>{nid()}</Id>
					<Expression>{cdata(data)}</Expression>
						<ColorPDF>{argb(col)}</ColorPDF>
						<ColorCDF>{argb(C['muted'])}</ColorCDF>
						<ColorLowPercent>{argb(C['faint'])}</ColorLowPercent>
						<ColorHighPercent>{argb(C['faint'])}</ColorHighPercent>
						<ColorMean>{argb(C['ink'])}</ColorMean>
						<LineWidth>1</LineWidth>
						<Title>{cdata(title)}</Title>
					</HistogramDataExpression>"""
    return f"""
    			<Histogram>
					<Id>{nid()}</Id>
					<Name>{cdata(name)}</Name>
					<X>{x}</X><Y>{y}</Y>
					<Label><X>0</X><Y>-10</Y></Label>
					<PublicFlag>true</PublicFlag>
					<PresentationFlag>true</PresentationFlag>
					<ShowLabel>false</ShowLabel>
					<DrawMode>SHAPE_DRAW_2D3D</DrawMode>
					<AutoUpdate>true</AutoUpdate>
					<OccurrenceAtTime>true</OccurrenceAtTime>
					<OccurrenceDate>1761535860000</OccurrenceDate>
					<OccurrenceTime Class="CodeUnitValue">
						{time_unit('60.5')}
					</OccurrenceTime>
					<RecurrenceCode Class="CodeUnitValue">
						{time_unit('60')}
					</RecurrenceCode>
					{chart_frame(w, h, 40, 10, w - 60, h - 60)}
					<ShowPDF>true</ShowPDF>
					<ShowCDF>false</ShowCDF>
					<ShowMean>true</ShowMean>
					<Bars>
						<Direction>UP</Direction>
						<RelativeWidth>0.8</RelativeWidth>
					</Bars>{ds}
    			</Histogram>"""


def edit_box(x, y, w, link, name, minv=None, maxv=None):
    lim = ""
    if minv is not None:
        lim += f"<MinValue>{cdata(str(minv))}</MinValue>"
    if maxv is not None:
        lim += f"<MaxValue>{cdata(str(maxv))}</MaxValue>"
    return (f"<Control Type=\"EditBox\"><EmbeddedIcon>false</EmbeddedIcon>{common(name, x, y)}"
            f"<DrawMode>SHAPE_DRAW_2D3D</DrawMode><BasicProperties Width=\"{w}\" Height=\"28\">"
            f"<EmbeddedIcon>false</EmbeddedIcon><FillColor/><TextColor/><Enabled>true</Enabled></BasicProperties>"
            f"<ExtendedProperties><Font Name=\"Dialog\" Size=\"12\" Style=\"0\"/>{lim}<LinkTo>true</LinkTo>"
            f"<Link>{link}</Link></ExtendedProperties></Control>")


def radio(x, y, w, h, buttons, link, name):
    b = "".join(f"<Button>{cdata(s)}</Button>" for s in buttons)
    return (f"<Control Type=\"RadioButtons\"><EmbeddedIcon>false</EmbeddedIcon>{common(name, x, y)}"
            f"<DrawMode>SHAPE_DRAW_2D3D</DrawMode><BasicProperties Width=\"{w}\" Height=\"{h}\">"
            f"<EmbeddedIcon>false</EmbeddedIcon><TextColor/><Enabled>true</Enabled></BasicProperties>"
            f"<ExtendedProperties><Font Name=\"Dialog\" Size=\"13\" Style=\"0\"/><DefaultValueCode>{cdata('0')}</DefaultValueCode>"
            f"<Orientation>VERTICAL</Orientation>{b}<LinkTo>true</LinkTo><Link>{link}</Link></ExtendedProperties></Control>")


# ==================================================================================================
# Java code of the model
# ==================================================================================================
ENGINE_SRC = open(os.path.join(ROOT, "engine", "FobEngine.java"), encoding="utf-8").read()

MAIN_ADDITIONAL = ENGINE_SRC + """

// ---- colours shared by Main and Passenger -------------------------------------------------
public static final Color C_PF1 = new Color(0xD9, 0x77, 0x06);      // amber  — direct PF1/PF1A
public static final Color C_FOB2 = new Color(0x00, 0xA1, 0x9B);     // teal   — FOB 2
public static final Color C_FOB3 = new Color(0x25, 0x63, 0xEB);     // blue   — FOB 3
public static final Color C_SKYWALK = new Color(0x7C, 0x3A, 0xED);  // purple — skywalk then FOB 3
public static final Color C_ENTER = new Color(0xD9, 0x30, 0x25);    // red  — passenger entering the station
public static final Color C_LEAVE = new Color(0x25, 0x63, 0xEB);    // blue — passenger leaving (returning)
"""

STARTUP = """// ---------------------------------------------------------------------
// Start-up: draw this run's route split (route-split noise), create one independent random
// stream per arrival stream and schedule the first arrivals. The same seed rules are used by
// FobEngine.runReplication, so this animated run equals replication 1 of the batch (seed = randomSeed).
// ---------------------------------------------------------------------
FobEngine.validateSplits(gateSplits);
FobEngine.validateExtraSplits(extraSplits);
java.util.Random noise = FobEngine.newSplitNoiseRandom(randomSeed);
splitsUsed = FobEngine.noisySplits(gateSplits, splitNoiseKappa, noise);
extraSplitsUsed = FobEngine.noisySplits(extraSplits, splitNoiseKappa, noise);
streamRng = new java.util.Random[FobEngine.NUM_STREAMS];
fob2PerMin = new int[durationMin];
fob3PerMin = new int[durationMin];
for (int s = 0; s < FobEngine.NUM_STREAMS; s++) {
	streamRng[s] = FobEngine.newStreamRandom(randomSeed, s);
	double lambda = FobEngine.ratePerMin(s, additionalDemand);
	if (lambda > 0) create_Arrival(FobEngine.drawInterarrivalSec(streamRng[s], lambda), s);
}
traceln("Kanjurmarg FOB model started: %s (+%.0f pax/min), seed %d, %d min", scenarioName, additionalDemand, randomSeed, durationMin);"""

FN_SPAWN = """// Create one passenger of the given stream on the chosen route and start walking.
int gate = FobEngine.gateOf(stream);
boolean entering = FobEngine.isEntering(stream);
Passenger p = add_passengers();
p.routeIdx = route;
p.entering = entering;
p.wpPath = FobEngine.waypoints(gate, entering, route);
p.wpIndex = 0;
p.jumpTo(toPxX(p.wpPath[0][0]), toPxY(p.wpPath[0][1]));
p.setSpeed(walkSpeed, MPS);
int fob = FobEngine.fobOf(route);
if (fob != 0) {
	// counted once, when the passenger reaches the FOB deck mid-point (skywalk users count on FOB 3)
	create_Crossing(FobEngine.crossingDelaySec(gate, entering, route, walkSpeed), fob);
}
advance(p);"""

FN_ADVANCE = """// Send the passenger to its next way-point, or remove it when the path is finished.
if (p.wpIndex >= p.wpPath.length - 1) {
	remove_passengers(p);
	return;
}
double[] a = p.wpPath[p.wpIndex];
double[] b = p.wpPath[p.wpIndex + 1];
p.moveTo(toPxX(b[0]), toPxY(b[1]));
create_Waypoint(FobEngine.segmentLength(a, b) / walkSpeed, p);"""

FN_TOPX = "return %g + xMetres * %g;" % (OX, PX_PER_M)
FN_TOPY = "return %g + yMetres * %g;" % (OY, PX_PER_M)
FN_CAP2 = "return FobEngine.capacityPerMin(fob2Width, flowIntensity);"
FN_CAP3 = "return FobEngine.capacityPerMin(fob3Width, flowIntensity);"

FN_HEAT = """// Deck colour for a utilization value: cool teal (low) -> amber (30%) -> red (60% and above)
double t = Math.max(0.0, Math.min(1.0, u / 60.0));
int[] low = {205, 237, 236}, mid = {253, 214, 130}, high = {239, 108, 96};
int[] from = t < 0.5 ? low : mid;
int[] to = t < 0.5 ? mid : high;
double k = t < 0.5 ? t / 0.5 : (t - 0.5) / 0.5;
return new Color((int) Math.round(from[0] + (to[0] - from[0]) * k),
                 (int) Math.round(from[1] + (to[1] - from[1]) * k),
                 (int) Math.round(from[2] + (to[2] - from[2]) * k));"""

EV_ARRIVAL = """// Poisson arrival for stream 'stream': choose the route with this gate's split, then schedule the next arrival.
if (time() >= durationMin * 60.0) return;            // arrivals stop at the end of the run
int gate = FobEngine.gateOf(stream);
int route = FobEngine.drawRoute(streamRng[stream], FobEngine.splitForStream(stream, splitsUsed, extraSplitsUsed));
spawnPassenger(stream, route);
double lambda = FobEngine.ratePerMin(stream, additionalDemand);
create_Arrival(FobEngine.drawInterarrivalSec(streamRng[stream], lambda), stream);"""

EV_WAYPOINT = """p.wpIndex++;
p.jumpTo(toPxX(p.wpPath[p.wpIndex][0]), toPxY(p.wpPath[p.wpIndex][1]));
advance(p);"""

EV_CROSSING = """// Count one FOB crossing in the one-minute interval in which it happens.
int minute = (int) Math.floor(time() / 60.0);
if (minute >= durationMin) return;
if (fob == 2) fob2PerMin[minute]++;
else if (fob == 3) fob3PerMin[minute]++;"""

EV_MINUTE = """// Close the one-minute interval that has just ended and update the utilization dashboard.
int m = (int) Math.round(time() / 60.0) - 1;
if (m < 0 || m >= durationMin) return;
lastU2 = fob2PerMin[m] / capacity2() * 100.0;
lastU3 = fob3PerMin[m] / capacity3() * 100.0;
peakU2 = Math.max(peakU2, lastU2);
peakU3 = Math.max(peakU3, lastU3);
sumU2 += lastU2;
sumU3 += lastU3;
minutesDone = m + 1;

// live gauges (full bar = 50% of reference capacity) and heat-coloured bridge decks
double full = 300;
barU2.setWidth(Math.max(1, Math.min(full, full * lastU2 / 50.0)));
barU3.setWidth(Math.max(1, Math.min(full, full * lastU3 / 50.0)));
fob2Deck.setFillColor(heatColor(lastU2));
fob3Deck.setFillColor(heatColor(lastU3));

if (minutesDone >= durationMin) {
	runFinished = true;
	traceln("Run complete: FOB 2 mean %.1f%% (peak %.1f%%), FOB 3 mean %.1f%% (peak %.1f%%)",
		sumU2 / minutesDone, peakU2, sumU3 / minutesDone, peakU3);
	getEngine().pause();
}"""

FN_BATCH = """// -----------------------------------------------------------------------------------------
// Replicated experiment: 'replications' runs for each scenario (+0, +50, +100 pax/min),
// seeds randomSeed .. randomSeed+replications-1 (common random numbers), route-split noise on.
// Same FobEngine code as the animation. Writes anylogic_batch_results.csv to the model folder.
// -----------------------------------------------------------------------------------------
double[] extra = {0, 50, 100};
String[] names = {"Baseline", "+50 pax/min", "+100 pax/min"};
double c2 = capacity2(), c3 = capacity3();
StringBuilder sb = new StringBuilder();
sb.append(String.format("%-6s %-4s %13s %6s%n", "Scen.", "FOB", "Mean U ±CI", "P95"));
java.io.PrintWriter out = null;
try {
	out = new java.io.PrintWriter("anylogic_batch_results.csv");
	out.println("scenario,additional_demand,replication,seed,facility,mean_util_pct,p95_util_pct,max_util_pct");
} catch (Exception e) {
	traceln("Could not open CSV file for writing: " + e);
}
for (int k = 0; k < 3; k++) {
	double[][] umean = new double[2][replications];
	double[][] up95 = new double[2][replications];
	double[][] umax = new double[2][replications];
	for (int r = 0; r < replications; r++) {
		long seed = randomSeed + r;
		FobEngine.Result res = FobEngine.runReplication(seed, extra[k], gateSplits, extraSplits, splitNoiseKappa, durationMin, walkSpeed);
		for (int f = 0; f < 2; f++) {
			int[] perMin = (f == 0) ? res.fob2PerMinute : res.fob3PerMinute;
			double cap = (f == 0) ? c2 : c3;
			double[] u = new double[perMin.length];
			for (int i = 0; i < perMin.length; i++) u[i] = perMin[i] / cap * 100.0;
			umean[f][r] = FobEngine.mean(u);
			up95[f][r] = FobEngine.percentile(u, 95);
			double mx = 0; for (double v : u) mx = Math.max(mx, v);
			umax[f][r] = mx;
			if (out != null) {
				out.println(String.format(java.util.Locale.ROOT, "%s,%.0f,%d,%d,%s,%.4f,%.4f,%.4f",
					names[k], extra[k], r + 1, seed, f == 0 ? "FOB 2" : "FOB 3", umean[f][r], up95[f][r], umax[f][r]));
			}
		}
	}
	for (int f = 0; f < 2; f++) {
		double ci = FobEngine.t95(replications - 1) * FobEngine.sampleStdDev(umean[f]) / Math.sqrt(replications);
		batchMeanU[k][f] = FobEngine.mean(umean[f]);
		sb.append(String.format("%-6s %-4s %7.1f%% \\u00b1%3.1f %5.1f%%%n", k == 0 ? "Base" : (k == 1 ? "+50" : "+100"),
			f == 0 ? "2" : "3", batchMeanU[k][f], ci, FobEngine.mean(up95[f])));
	}
}
if (out != null) out.close();
batchSummary = sb.toString();
batchDone = true;

traceln(batchSummary);"""

PASSENGER_CLASS_ID = nid()
PASSENGER_GEN_ID = nid()
MAIN_CLASS_ID = nid()
MAIN_GEN_ID = nid()


def passenger_class():
    lvl = nid()
    pres = oval(0, 0, 3.2, C["teal"],
                fill_code="entering ? Main.C_ENTER : Main.C_LEAVE",
                name="body", line="#FFFFFF")
    return agent_header(PASSENGER_CLASS_ID, "Passenger", PASSENGER_GEN_ID) + agent_props() + env_props(500, 500) + \
        scale_ruler(True) + f"""
			<CurrentLevel>{lvl}</CurrentLevel>
			<ConnectionsId>{nid()}</ConnectionsId>
			<Variables>""" + \
        plain_var("routeIdx", "int", "0", 50, 50) + \
        plain_var("entering", "boolean", "true", 50, 140) + \
        plain_var("wpPath", "double[][]", None, 50, 80) + \
        plain_var("wpIndex", "int", "0", 50, 110) + f"""
			</Variables>
			<ContainerLinks>
				<ContainerLink>
					<Id>{nid()}</Id>
					<Name>{cdata('main')}</Name>
					<X>200</X><Y>50</Y>
					<Label><X>10</X><Y>0</Y></Label>
					<PublicFlag>false</PublicFlag>
					<PresentationFlag>true</PresentationFlag>
					<ShowLabel>true</ShowLabel>
					<ActiveObjectClass>
						<PackageName>{cdata(PKG)}</PackageName>
						<ClassName>{cdata('Main')}</ClassName>
					</ActiveObjectClass>
				</ContainerLink>
			</ContainerLinks>
			<Presentation>
				<Level>
					<Id>{lvl}</Id>
					<Name>{cdata('level')}</Name>
					<X>0</X><Y>0</Y>
					<Label><X>10</X><Y>0</Y></Label>
					<PublicFlag>true</PublicFlag>
					<PresentationFlag>true</PresentationFlag>
					<ShowLabel>false</ShowLabel>
					<DrawMode>SHAPE_DRAW_2D3D</DrawMode>
					<Z>0</Z>
					<LevelVisibility>DIM_NON_CURRENT</LevelVisibility>
			<Presentation>
				{pres}
			</Presentation>
				</Level>
			</Presentation>
		</ActiveObjectClass>"""


# ------------------------------------------------------------------ station layout (pixels)
TOP, BOT = 2.0, 90.0          # platform / track extent (m)
LAYOUT_W = 86.0               # layout width (m)


def tree(xm, ym, r=1.6):
    return [oval(X(xm) + 1.5, Y(ym) + 1.5, M(r), "#C9D3C3"), oval(X(xm), Y(ym), M(r), C["tree"], line=C["tree_dark"])]


def train(x_center, y0, y1, name):
    """A parked suburban EMU drawn as coaches with windows (purely decorative)."""
    s = []
    w = 3.4
    coach = 9.0
    y = y0
    k = 0
    while y + coach <= y1 + 0.01:
        x0 = x_center - w / 2
        s.append(rrect(X(x0), Y(y), M(w), M(coach - 0.5), 6, fill=C["train_body"], line="#8E8778", lw=1, name=f"{name}_c{k}"))
        s.append(rect(X(x0 + 0.5), Y(y + 0.4), M(w - 1.0), M(coach - 1.3), fill=C["train_roof"], line=None, lw=0))
        s.append(rect(X(x0), Y(y + 0.2), M(0.35), M(coach - 0.9), fill=C["train_stripe"], line=None, lw=0))
        s.append(rect(X(x0 + w - 0.35), Y(y + 0.2), M(0.35), M(coach - 0.9), fill=C["train_stripe"], line=None, lw=0))
        for j in range(4):
            s.append(rect(X(x0 + 0.9), Y(y + 0.9 + j * 2.0), M(w - 1.8), M(1.1), fill=C["train_window"], line=None, lw=0))
        y += coach
        k += 1
    return s


def track(x_center):
    s = []
    gauge = 1.7
    sl = 2.6
    yy = TOP + 1.0
    while yy < BOT:
        s.append(poly([(X(x_center - sl / 2), Y(yy)), (X(x_center + sl / 2), Y(yy))], C["sleeper"], 2.5))
        yy += 2.0
    for dx in (-gauge / 2, gauge / 2):
        s.append(poly([(X(x_center + dx), Y(TOP)), (X(x_center + dx), Y(BOT))], C["rail"], 1.6))
    return s


def platform(x0, x1, label, edges):
    s = [rect(X(x0), Y(TOP), M(x1 - x0), M(BOT - TOP), fill=C["platform"], line=C["platform_edge"])]
    cx = (x0 + x1) / 2
    s.append(rrect(X(cx - 2.6), Y(TOP + 3), M(5.2), M(BOT - TOP - 6), 10, fill=C["canopy"], line=None, lw=0))
    for yy in range(int(TOP + 6), int(BOT - 4), 6):
        s.append(poly([(X(cx - 2.6), Y(yy)), (X(cx + 2.6), Y(yy))], "#AEB7C2", 1))
    for ex in edges:
        s.append(poly([(X(ex), Y(TOP)), (X(ex), Y(BOT))], C["safety"], 2.5, style="DASHED"))
    s.append(rrect(X(cx) - 34, Y(71) - 13, 68, 20, 10, fill="#FFFFFF", line=C["platform_edge"]))
    s.append(text(X(cx), Y(71) + 2, label, 12, "ink", True, "CENTER"))
    return s


def stairs(xm, ym, horizontal=True, col=C["muted"]):
    """Small stair glyph at a bridge landing."""
    s = [rect(X(xm) - 7, Y(ym) - 7, 14, 14, fill="#FFFFFF", line=col, lw=1)]
    for i in range(4):
        if horizontal:
            s.append(poly([(X(xm) - 5, Y(ym) - 4.5 + i * 3), (X(xm) + 5, Y(ym) - 4.5 + i * 3)], col, 1))
        else:
            s.append(poly([(X(xm) - 4.5 + i * 3, Y(ym) - 5), (X(xm) - 4.5 + i * 3, Y(ym) + 5)], col, 1))
    return s


def gate_marker(xm, ym, code, label, label_dx, align, col=C["ink"]):
    """Gate: a large coloured disc with its code and a white name tag above it."""
    w = len(label) * 7.6 + 22
    s = [oval(X(xm), Y(ym), 16, col, line="#FFFFFF", lw=2.5),
         text(X(xm), Y(ym) + 5, code, 11 if len(code) > 1 else 14, "#FFFFFF", True, "CENTER"),
         rrect(X(xm) + label_dx - w / 2, Y(ym) - 44, w, 22, 11, fill="#FFFFFF", line=col, lw=1.8),
         text(X(xm) + label_dx, Y(ym) - 28, label, 12, col, True, "CENTER")]
    return s


def layout_shapes():
    s = []
    s.append(rect(0, 0, 1480, 1100, fill=C["bg"], line=None, lw=0, name="canvasBg"))
    s.append(text(OX, 34, "Kanjurmarg Station — Foot Overbridge Utilization", 22, "ink", True, name="titleText"))

    # layout card + ground
    s.append(rrect(OX - 25, OY - 50, M(LAYOUT_W) + 50, M(BOT + 4) + 105, 10, fill=C["card"], line=C["cardline"]))
    s.append(rect(X(0), Y(0), M(LAYOUT_W), M(BOT + 2), fill=C["ground"], line=None, lw=0))
    s.append(text(OX - 8, OY - 28, "STATION LAYOUT", 11, "muted", True))

    # roads (west and east) with centre dashes
    for x0, x1 in ((0, 7), (78, 86)):
        s.append(rect(X(x0), Y(0), M(x1 - x0), M(BOT + 2), fill=C["road"], line=None, lw=0))
        s.append(poly([(X((x0 + x1) / 2), Y(1)), (X((x0 + x1) / 2), Y(BOT + 1))], C["roadline"], 1.5, style="DASHED"))

    # west paved concourse
    s.append(rect(X(8), Y(TOP), M(8), M(BOT - TOP), fill=C["paving"], line="#D6CFC2"))
    for yy in range(4, 90, 4):
        s.append(poly([(X(8), Y(yy)), (X(16), Y(yy))], "#DDD6CA", 1))

    # trees along the roads
    for ym in (6, 24, 39, 54, 69, 86):
        s += tree(7.6, ym, 1.4)

    # platforms
    s += platform(18, 30, "PF 1", (29.6,))
    s += platform(42, 54, "PF 2", (42.4, 53.6))

    # track beds with sleepers and rails
    for x0 in (30, 54):
        s.append(rect(X(x0), Y(TOP), M(12), M(BOT - TOP), fill=C["ballast"], line=None, lw=0))
    for xc in (33, 39, 57, 63):
        s += track(xc)
    # parked trains (decorative)

    # east side strip for the skywalk
    s.append(rect(X(66), Y(TOP), M(12), M(BOT - TOP), fill="#F1EEF8", line=None, lw=0))
    for ym in (5, 24, 40, 55, 70, 88):
        s += tree(66.9, ym, 0.9)

    # FOB decks (drawn over tracks and trains). Fill colour of FOB 2 / FOB 3 changes with utilization.
    def deck(yc, width_m, col, fill, name, closed=False):
        x_end = 64 if closed else 70
        out = [rect(X(12), Y(yc - width_m / 2), M(x_end - 12), M(width_m), fill=fill, line=col, lw=2.2, name=name,
                    style="DASHED" if closed else "SOLID")]
        out.append(poly([(X(12), Y(yc - width_m / 2) + 3), (X(x_end), Y(yc - width_m / 2) + 3)], col, 0.8))
        out.append(poly([(X(12), Y(yc + width_m / 2) - 3), (X(x_end), Y(yc + width_m / 2) - 3)], col, 0.8))
        return out

    s += deck(8, 3.6, C["red"], C["red_soft"], "fob1Deck", closed=True)
    for xx in (16, 24, 48, 56):
        s.append(poly([(X(xx), Y(6.8)), (X(xx + 2.4), Y(9.2))], C["red"], 2))
        s.append(poly([(X(xx), Y(9.2)), (X(xx + 2.4), Y(6.8))], C["red"], 2))
    s.append(rrect(X(38) - 70, Y(8) - 10, 140, 20, 10, fill=C["red"], line=None, lw=0))
    s.append(text(X(38), Y(8) + 4, "FOB 1 · CLOSED", 11, "#FFFFFF", True, "CENTER"))

    # skywalk: elevated connector between FOB 2 and FOB 3, with NE and SE exits
    s.append(rect(X(68), Y(6.5), M(4), M(75), fill=C["purple_soft"], line=C["purple"], lw=2, name="skywalkDeck"))
    s.append(poly([(X(68.6), Y(7)), (X(68.6), Y(81))], C["purple"], 0.8))
    s.append(poly([(X(71.4), Y(7)), (X(71.4), Y(81))], C["purple"], 0.8))
    s.append(rect(X(70), Y(6.5), M(8), M(3), fill=C["purple_soft"], line=C["purple"], lw=1.5))
    s.append(rect(X(70), Y(78.5), M(8), M(3), fill=C["purple_soft"], line=C["purple"], lw=1.5))
    s.append(text(X(73.8), Y(47), "SKYWALK", 10, "purple", True, "CENTER"))

    s += deck(32, 5.36, C["teal"], C["teal_soft"], "fob2Deck")
    s += deck(62, 6.0, C["blue"], C["blue_soft"], "fob3Deck")
    for yc, w, col, lab in ((32, 5.36, C["teal"], "FOB 2 · 5.36 m"), (62, 6.0, C["blue"], "FOB 3 · 6.0 m")):
        s.append(poly([(X(36), Y(yc - w / 2)), (X(36), Y(yc + w / 2))], col, 2, style="DOTTED"))
        s.append(rrect(X(50) - 66, Y(yc - w / 2) - 22, 132, 18, 9, fill=col, line=None, lw=0))
        s.append(text(X(50), Y(yc - w / 2) - 9, lab, 11, "#FFFFFF", True, "CENTER"))

    # stair landings
    for yc in (32, 62):
        s += stairs(12, yc, horizontal=False)
        s += stairs(24, yc + (6 if yc == 32 else -6))
        s += stairs(48, yc + 6)
    s += stairs(24, 26)

    # gates
    s += gate_marker(4, 16, "N", "Naval Colony", 12, "CENTER")
    s += gate_marker(4, 46, "H", "Huma", 12, "CENTER")
    s += gate_marker(4, 78, "G", "Gandhi Nagar", 12, "CENTER")
    s += gate_marker(80, 8, "NE", "Northeast", -6, "CENTER", col=C["purple"])
    s += gate_marker(80, 80, "SE", "Southeast", -6, "CENTER", col=C["purple"])

    # north arrow
    nx, ny = X(LAYOUT_W) - 4, OY - 30
    s.append(poly([(nx, ny + 18), (nx, ny - 6)], C["ink"], 2))
    s.append(poly([(nx - 5, ny + 2), (nx, ny - 8), (nx + 5, ny + 2)], C["ink"], 2, closed=True, fill=C["ink"]))
    s.append(text(nx - 10, ny + 4, "N", 12, "ink", True, "RIGHT"))

    # legend
    ly = Y(BOT + 2) + 42
    items = (("Entering passenger", C["red"]), ("Leaving (returning) passenger", C["blue"]))
    for i, (lab, col) in enumerate(items):
        lx = X(1) + i * 170
        s.append(oval(lx, ly, 5, col, line="#FFFFFF"))
        s.append(text(lx + 11, ly + 4, lab, 11, "ink"))
    hy = ly + 24
    s.append(text(X(1) - 5, hy + 4, "Deck colour = live 1-min utilization:", 11, "muted"))
    for i, (lab, col) in enumerate((("0%", "#CDEDEC"), ("30%", "#FDD682"), ("≥60%", "#EF6C60"))):
        bx = X(1) + 215 + i * 70
        s.append(rrect(bx, hy - 7, 26, 14, 4, fill=col, line=C["cardline"]))
        s.append(text(bx + 31, hy + 4, lab, 10, "muted"))
    return s


# ------------------------------------------------------------------ utilization dashboard (right side)
DX = 760
DW = 700


def dashboard_shapes():
    s = []
    y = OY - 50
    s.append(card(DX, y, DW, 70, accent=C["teal"]))
    s.append(text(DX + 20, y + 24, "Scenario", 11, "muted", True))
    s.append(text(DX + 20, y + 50, "", 17, "ink", True,
                  code='scenarioName + "   ·   +" + String.format("%.0f", additionalDemand) + " pax/min extra"', name="txtScenario"))
    s.append(text(DX + 470, y + 24, "Model clock", 11, "muted", True))
    s.append(text(DX + 470, y + 50, "", 17, "ink", True, font="Monospaced",
                  code='String.format("%02d:%02d / %d:00", (int)(time() / 60), (int)(time() % 60), durationMin) + (runFinished ? "  done" : "")',
                  name="txtClock"))

    # two utilization gauge cards
    y = OY + 30
    for i, (fob, col, idx, wtxt) in enumerate((("FOB 2", C["teal"], 2, "W 5.36 m · C = "), ("FOB 3", C["blue"], 3, "W 6.0 m · C = "))):
        x = DX + i * 356
        s.append(card(x, y, 344, 196, accent=col))
        s.append(text(x + 20, y + 26, fob + " UTILIZATION", 13, col, True))
        s.append(text(x + 20, y + 44, "", 10, "muted",
                      code=f'"{wtxt}" + String.format("%.1f pax/min", capacity{idx}())', name=f"txtCap{idx}"))
        s.append(text(x + 20, y + 98, "", 40, "ink", True,
                      code=f'minutesDone == 0 ? "–" : String.format("%.1f%%", lastU{idx})', name=f"txtNow{idx}"))
        s.append(text(x + 20, y + 116, "last full minute", 10, "muted"))
        s.append(text(x + 200, y + 72, "Mean", 10, "muted", True))
        s.append(text(x + 200, y + 92, "", 16, "ink", True,
                      code=f'minutesDone == 0 ? "–" : String.format("%.1f%%", sumU{idx} / minutesDone)', name=f"txtMean{idx}"))
        s.append(text(x + 268, y + 72, "Peak", 10, "muted", True))
        s.append(text(x + 268, y + 92, "", 16, "ink", True,
                      code=f'minutesDone == 0 ? "–" : String.format("%.1f%%", peakU{idx})', name=f"txtPeak{idx}"))
        # gauge 0–50 %
        gx, gy = x + 20, y + 140
        s.append(rrect(gx, gy, 300, 16, 8, fill="#EEF1F4", line=None, lw=0))
        s.append(rect(gx, gy, 1, 16, fill=col, line=None, lw=0, name=f"barU{idx}"))
        for t in range(0, 51, 10):
            tx = gx + 300 * t / 50
            s.append(poly([(tx, gy + 18), (tx, gy + 23)], C["faint"], 1))
            s.append(text(tx, gy + 36, f"{t}%", 9, "muted", align="CENTER"))

    # one-minute utilization over time
    y = OY + 236
    s.append(card(DX, y, DW, 300))
    s.append(text(DX + 16, y + 22, "One-minute utilization over the hour (% of reference capacity)", 12, "ink", True))
    return s


def controls():
    y = OY + 546
    return [
        button(DX + 410, y, 140, 32, "Run replications", "runBatch();", "btnBatch"),
        button(DX + 560, y, 120, 32, "Pause / Resume",
               "if (getEngine().getState() == Engine.State.RUNNING) getEngine().pause(); else getEngine().run();",
               "btnPause"),
    ]


def main_class():
    lvl = nid()
    pop_pres_id = nid()
    params = (
        parameter("scenarioName", "String", '"Baseline"', -350, 40, "Scenario name") +
        parameter("additionalDemand", "double", "0", -350, 70, "Additional demand (pax/min)") +
        parameter("gateSplits", "double[][]", "FobEngine.defaultGateSplits()", -350, 110, "Route split per gate {PF1, FOB2, FOB3, skywalk}") +
        parameter("extraSplits", "double[][]", "FobEngine.defaultExtraSplits()", -350, 125, "Route split of additional demand {Huma, Gandhi Nagar}") +
        parameter("splitNoiseKappa", "double", "99", -350, 140, "Route-split noise concentration (0 = off)") +
        parameter("randomSeed", "long", "1001", -350, 180, "Random seed") +
        parameter("durationMin", "int", "60", -350, 210, "Run duration (min)") +
        parameter("replications", "int", "30", -350, 240, "Replications (batch)") +
        parameter("fob2Width", "double", "5.36", -350, 280, "FOB 2 width (m)") +
        parameter("fob3Width", "double", "6.0", -350, 310, "FOB 3 width (m) - assumed") +
        parameter("flowIntensity", "double", "60", -350, 340, "Flow intensity I (pax/m/min)") +
        parameter("walkSpeed", "double", "1.30", -350, 370, "Walking speed (m/s)")
    )
    var_specs = [
        ("streamRng", "java.util.Random[]", None), ("splitsUsed", "double[][]", None), ("extraSplitsUsed", "double[][]", None),
        ("fob2PerMin", "int[]", None), ("fob3PerMin", "int[]", None),
        ("lastU2", "double", "0"), ("lastU3", "double", "0"), ("peakU2", "double", "0"), ("peakU3", "double", "0"),
        ("sumU2", "double", "0"), ("sumU3", "double", "0"), ("minutesDone", "int", "0"),
        ("runFinished", "boolean", "false"), ("batchDone", "boolean", "false"),
        ("batchSummary", "String", '""'), ("batchMeanU", "double[][]", "new double[3][2]"),
    ]
    variables = "".join(plain_var(n, t, i, -200, 40 + 26 * k) for k, (n, t, i) in enumerate(var_specs))
    events = cyclic_event("minuteTick", "60", "60", EV_MINUTE, -500, 40)
    dyn = (dynamic_event("Arrival", [("stream", "int")], EV_ARRIVAL, -500, 90) +
           dynamic_event("Waypoint", [("p", "Passenger")], EV_WAYPOINT, -500, 120) +
           dynamic_event("Crossing", [("fob", "int")], EV_CROSSING, -500, 150))
    funcs = (
        function("spawnPassenger", "double", FN_SPAWN, -500, 230, params=[("stream", "int"), ("route", "int")]) +
        function("advance", "double", FN_ADVANCE, -500, 260, params=[("p", "Passenger")]) +
        function("toPxX", "double", FN_TOPX, -500, 290, params=[("xMetres", "double")], returns=True) +
        function("toPxY", "double", FN_TOPY, -500, 320, params=[("yMetres", "double")], returns=True) +
        function("capacity2", "double", FN_CAP2, -500, 350, returns=True) +
        function("capacity3", "double", FN_CAP3, -500, 380, returns=True) +
        function("heatColor", "Color", FN_HEAT, -500, 410, params=[("u", "double")], returns=True) +
        function("runBatch", "double", FN_BATCH, -500, 470)
    )
    analysis = ""
    population = f"""
				<EmbeddedObject>
					<Id>{nid()}</Id>
					<Name>{cdata('passengers')}</Name>
					<X>-650</X><Y>120</Y>
					<Label><X>-30</X><Y>-30</Y></Label>
					<PublicFlag>false</PublicFlag>
					<PresentationFlag>true</PresentationFlag>
					<ShowLabel>true</ShowLabel>
					<PresentationId>{pop_pres_id}</PresentationId>
					<ActiveObjectClass>
						<PackageName>{cdata(PKG)}</PackageName>
						<ClassName>{cdata('Passenger')}</ClassName>
					</ActiveObjectClass>
					<GenericParameterSubstitute>
						<GenericParameterSubstituteReference>
							<PackageName>{cdata(PKG)}</PackageName>
							<ClassName>{cdata('Passenger')}</ClassName>
							<ItemName>{cdata(str(PASSENGER_GEN_ID))}</ItemName>
						</GenericParameterSubstituteReference>
					</GenericParameterSubstitute>
					<Parameters>
					</Parameters>
					<ReplicationFlag>true</ReplicationFlag>
					<Replication Class="CodeValue">
						<Code>{cdata('0')}</Code>
					</Replication>
					<CollectionType>ARRAY_LIST_BASED</CollectionType>
					<InEnvironment>true</InEnvironment>
					<InitialLocationType>AT_ANIMATION_POSITION</InitialLocationType>
					<XCode Class="CodeValue"><Code>{cdata('0')}</Code></XCode>
					<YCode Class="CodeValue"><Code>{cdata('0')}</Code></YCode>
					<ZCode Class="CodeValue"><Code>{cdata('0')}</Code></ZCode>
					<ColumnCode Class="CodeValue"><Code>{cdata('0')}</Code></ColumnCode>
					<RowCode Class="CodeValue"><Code>{cdata('0')}</Code></RowCode>
					<LatitudeCode Class="CodeValue"><Code>{cdata('0')}</Code></LatitudeCode>
					<LongitudeCode Class="CodeValue"><Code>{cdata('0')}</Code></LongitudeCode>
					<LocationNameCode Class="CodeValue"><Code>{cdata('""')}</Code></LocationNameCode>
					<InitializationType>SPECIFIED_NUMBER</InitializationType>
					<InitializationDatabaseTableQuery>
						<TableReference>
						</TableReference>
					</InitializationDatabaseTableQuery>
					<InitializationDatabaseType>ONE_AGENT_PER_DATABASE_RECORD</InitializationDatabaseType>
					<QuantityColumn>
					</QuantityColumn>
				</EmbeddedObject>"""
    pop_pres = f"""
				<EmbeddedObjectPresentation>
					<Id>{pop_pres_id}</Id>
					<Name>{cdata('passengers_presentation')}</Name>
					<X>0</X><Y>0</Y>
					<Label><X>10</X><Y>0</Y></Label>
					<PublicFlag>true</PublicFlag>
					<PresentationFlag>true</PresentationFlag>
					<ShowLabel>false</ShowLabel>
					<DrawMode>SHAPE_DRAW_2D3D</DrawMode>
					<EmbeddedIcon>false</EmbeddedIcon>
					<Z>0</Z>
					<Rotation>0.0</Rotation>
					<DrawingMode>POSITION_WITH_OFFSET</DrawingMode>
					<ScaleType>AUTOMATICALLY_CALCULATED</ScaleType>
					<GISScaleForRealEmbeddedObjectPresentationSize>1000</GISScaleForRealEmbeddedObjectPresentationSize>
					<GISScaleForFixedEmbeddedObjectPresentationSize>1000000000</GISScaleForFixedEmbeddedObjectPresentationSize>
					<Latitude>0.0</Latitude>
					<Longitude>0.0</Longitude>
				</EmbeddedObjectPresentation>"""
    charts = time_plot("utilPlot", DX + 8, OY + 266, DW - 16, 266,
                       [("FOB 2", "lastU2", C["teal"]), ("FOB 3", "lastU3", C["blue"])], 50)
    shapes = "\n".join(layout_shapes()) + "\n" + "\n".join(dashboard_shapes())
    presentation = shapes + pop_pres + charts + "\n".join(controls())

    extra = (f"<AdditionalClassCode>{cdata(MAIN_ADDITIONAL)}</AdditionalClassCode>"
             f"<Import>{cdata('import java.awt.Color;')}</Import><StartupCode>{cdata(STARTUP)}</StartupCode>")
    return agent_header(MAIN_CLASS_ID, "Main", MAIN_GEN_ID, extra) + agent_props() + env_props(1480, 1100) + \
        scale_ruler(False) + f"""
			<CurrentLevel>{lvl}</CurrentLevel>
			<ConnectionsId>{nid()}</ConnectionsId>
			<Variables>{params}{variables}
			</Variables>
			<Events>{events}
			</Events>
			<DynamicEvents>{dyn}
			</DynamicEvents>
			<Functions>{funcs}
			</Functions>
			<AnalysisData>{analysis}
			</AnalysisData>
			<EmbeddedObjects>{population}
			</EmbeddedObjects>
			<Presentation>
				<Level>
					<Id>{lvl}</Id>
					<Name>{cdata('level')}</Name>
					<X>0</X><Y>0</Y>
					<Label><X>10</X><Y>0</Y></Label>
					<PublicFlag>true</PublicFlag>
					<PresentationFlag>true</PresentationFlag>
					<ShowLabel>false</ShowLabel>
					<DrawMode>SHAPE_DRAW_2D3D</DrawMode>
					<Z>0</Z>
					<LevelVisibility>DIM_NON_CURRENT</LevelVisibility>
			<Presentation>
{presentation}
			</Presentation>
				</Level>
			</Presentation>
		</ActiveObjectClass>"""


def experiment():
    ex_vars = (plain_var("scenarioIdx", "int", "0", -100, 40) + plain_var("seedVal", "int", "1001", -100, 70) +
               plain_var("repsVal", "int", "30", -100, 100) + plain_var("durVal", "int", "60", -100, 130) +
               plain_var("w3Val", "double", "6.0", -100, 160) + plain_var("kappaVal", "double", "99", -100, 190))
    pres = [
        rect(0, 0, 900, 620, fill=C["bg"], line=None, lw=0),
        card(40, 30, 820, 80, accent=C["teal"]),
        text(62, 78, "Kanjurmarg FOB Utilization — Stochastic Simulation", 22, "ink", True),
        card(40, 160, 400, 250),
        text(60, 188, "ADDITIONAL DEMAND SCENARIO", 11, "muted", True),
        radio(60, 205, 370, 100, ["Baseline (+0 pax/min)", "+50 pax/min  (10% of Ghatkopar reference)",
                                  "+100 pax/min (20% of Ghatkopar reference)"], "scenarioIdx", "rbScenario"),
        text(60, 330, "Extra entering demand: 80% Huma, 20% Gandhi Nagar.", 11, "muted"),
        card(460, 160, 400, 250),
        text(480, 188, "RUN SETTINGS", 11, "muted", True),
    ]
    rows = [("Random seed", "seedVal", 0, None), ("Replications (batch)", "repsVal", 2, 500),
            ("Run duration (min)", "durVal", 1, 600), ("FOB 3 width (m)", "w3Val", 1, 20),
            ("Route-split noise (99; 0 = off)", "kappaVal", 0, 100000)]
    for i, (lab, link, mn, mx) in enumerate(rows):
        yy = 205 + i * 38
        pres.append(text(480, yy + 19, lab, 13, "ink"))
        pres.append(edit_box(700, yy, 140, link, f"eb_{link}", mn, mx))
    pres += [
        card(40, 430, 820, 120),
        text(60, 458, "HOW TO USE", 11, "muted", True),
        text(60, 482, "1. Choose a scenario and press Run.  2. Bridge decks change colour with live one-minute utilization U = Q / (W × 60) × 100%.", 12, "ink"),
        text(60, 502, "3. The dashboard shows FOB 2 and FOB 3 utilization: now, mean, peak and a time plot.", 12, "ink"),
        text(60, 522, "4. 'Run replications' runs all three scenarios and writes mean utilization (95% CI) to the console and anylogic_batch_results.csv.", 12, "ink"),
    ]
    params_xml = ""
    pmap = {
        "scenarioName": 'scenarioIdx == 0 ? "Baseline" : (scenarioIdx == 1 ? "+50 pax/min" : "+100 pax/min")',
        "additionalDemand": "scenarioIdx == 0 ? 0.0 : (scenarioIdx == 1 ? 50.0 : 100.0)",
        "gateSplits": None, "extraSplits": None, "splitNoiseKappa": "kappaVal",
        "randomSeed": "seedVal", "durationMin": "durVal", "replications": "repsVal",
        "fob2Width": None, "fob3Width": "w3Val", "flowIntensity": None, "walkSpeed": None,
    }
    for k, v in pmap.items():
        val = "" if v is None else f"<ParameterValue Class=\"CodeValue\"><Code>{cdata(v)}</Code></ParameterValue>"
        params_xml += f"<Parameter><ParameterName>{cdata(k)}</ParameterName>{val}</Parameter>\n"
    return f"""
		<SimulationExperiment ActiveObjectClassId="{MAIN_CLASS_ID}">
			<Id>{nid()}</Id>
			<Name>{cdata('Simulation')}</Name>
			<CommandLineArguments>{cdata('')}</CommandLineArguments>
			<MaximumMemory>1024</MaximumMemory>
			<RandomNumberGenerationType>fixedSeed</RandomNumberGenerationType>
			<CustomGeneratorCode>new Random()</CustomGeneratorCode>
			<SeedValue>1001</SeedValue>
			<SelectionModeForSimultaneousEvents>LIFO</SelectionModeForSimultaneousEvents>
			<VmArgs>{cdata('')}</VmArgs>
			<LoadRootFromSnapshot>false</LoadRootFromSnapshot>
			<Variables>{ex_vars}
			</Variables>
			<Presentation>
{chr(10).join(pres)}
			</Presentation>
			<Parameters>
{params_xml}
			</Parameters>
			<PresentationProperties>
				<EnableZoomAndPanning>true</EnableZoomAndPanning>
				<ExecutionMode>{cdata('realTimeScaled')}</ExecutionMode>
				<Title>{cdata('Kanjurmarg FOB Utilization : Simulation')}</Title>
				<EnableDeveloperPanel>true</EnableDeveloperPanel>
				<ShowDeveloperPanelOnStart>false</ShowDeveloperPanelOnStart>
				<RealTimeScale>10.0</RealTimeScale>
			</PresentationProperties>
			<ModelTimeProperties>
				<StopOption>{cdata('Never')}</StopOption>
				<InitialDate>{cdata('1761535800000')}</InitialDate>
				<InitialTime>{cdata('0.0')}</InitialTime>
				<FinalDate>{cdata('1761539400000')}</FinalDate>
				<FinalTime>{cdata('3600.0')}</FinalTime>
			</ModelTimeProperties>
			<BypassInitialScreen>false</BypassInitialScreen>
		</SimulationExperiment>"""


def build():
    model_id = nid()
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!--
*************************************************
	         AnyLogic Project File
*************************************************
-->
<AnyLogicWorkspace WorkspaceVersion="1.9" AnyLogicVersion="8.8.6.202312140435" AlpVersion="8.8.3">
<Model>
	<Id>{model_id}</Id>
	<Name>{cdata(MODEL_NAME)}</Name>
	<Description>{cdata('Stochastic simulation of foot-overbridge (FOB) utilization at Kanjurmarg railway station. Five gates (Naval Colony, Huma, Gandhi Nagar, Northeast, Southeast); route split per gate with route-split noise; FOB 1 closed; skywalk connects FOB 2 and FOB 3 on the east side. Scenarios: baseline, +50 and +100 pax/min extra entering demand (10% / 20% of an assumed 500 pax/min Ghatkopar reference), 80% via Huma and 20% via Gandhi Nagar. Simplified conceptual layout - not to scale. IE 301 project.')}</Description>
	<EngineVersion>6</EngineVersion>
	<JavaPackageName>{cdata(PKG)}</JavaPackageName>
	<ModelTimeUnit>{cdata('Second')}</ModelTimeUnit>
	<ActiveObjectClasses>
		<!--   =========   Active Object Class   ========  -->{main_class()}
		<!--   =========   Active Object Class   ========  -->{passenger_class()}
	</ActiveObjectClasses>
	<DifferentialEquationsMethod>EULER</DifferentialEquationsMethod>
	<MixedEquationsMethod>RK45_NEWTON</MixedEquationsMethod>
	<AlgebraicEquationsMethod>MODIFIED_NEWTON</AlgebraicEquationsMethod>
	<AbsoluteAccuracy>1.0E-5</AbsoluteAccuracy>
	<FixedTimeStep>0.001</FixedTimeStep>
	<RelativeAccuracy>1.0E-5</RelativeAccuracy>
	<TimeAccuracy>1.0E-5</TimeAccuracy>
	<Frame>
		<Width>1480</Width>
		<Height>1100</Height>
	</Frame>
	<Database>
		<Logging>false</Logging>
		<AutoExport>false</AutoExport>
		<ShutdownCompact>false</ShutdownCompact>
		<ImportSettings>
		</ImportSettings>
		<ExportSettings>
		</ExportSettings>
	</Database>

	<RunConfiguration ActiveObjectClassId="{MAIN_CLASS_ID}">
		<Id>{nid()}</Id>
		<Name>{cdata('RunConfiguration')}</Name>
		<MaximumMemory>1024</MaximumMemory>
		<ModelTimeProperties>
			<StopOption>{cdata('Never')}</StopOption>
			<InitialDate>{cdata('1761535800000')}</InitialDate>
			<InitialTime>{cdata('0.0')}</InitialTime>
			<FinalDate>{cdata('1761539400000')}</FinalDate>
			<FinalTime>{cdata('3600.0')}</FinalTime>
		</ModelTimeProperties>
		<AnimationProperties>
			<StopNever>true</StopNever>
			<ExecutionMode>realTimeScaled</ExecutionMode>
			<RealTimeScale>10.0</RealTimeScale>
			<EnableZoomAndPanning>true</EnableZoomAndPanning>
			<EnableDeveloperPanel>false</EnableDeveloperPanel>
			<ShowDeveloperPanelOnStart>false</ShowDeveloperPanelOnStart>
		</AnimationProperties>
		<Inputs>
		</Inputs>
		<Outputs>
		</Outputs>
	</RunConfiguration>
	<Experiments>
		<!--   =========   Simulation Experiment   ========  -->{experiment()}
	</Experiments>
    <RequiredLibraryReference>
		<LibraryName>{cdata('com.anylogic.libraries.modules.markup_descriptors')}</LibraryName>
		<VersionMajor>1</VersionMajor>
		<VersionMinor>0</VersionMinor>
		<VersionBuild>0</VersionBuild>
    </RequiredLibraryReference>
</Model>
</AnyLogicWorkspace>
"""
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, MODEL_NAME + ".alp")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(xml)
    print("wrote", path, len(xml), "bytes")
    return path


if __name__ == "__main__":
    build()
